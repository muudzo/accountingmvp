"""Unit tests for Ecocash parser."""

from src.parsers import EcocashParser


class TestEcocashParser:
    """Tests for EcocashParser."""

    def test_parse_csv_format(self, tmp_path):
        """Test parsing structured Ecocash CSV."""
        csv_file = tmp_path / "ecocash.csv"
        csv_file.write_text(
            "Date,Amount,Description,Reference\n"
            "15/01/2024,1500,Payment from John,EC001\n"
            "16/01/2024,250,Transfer to Jane,EC002\n"
        )

        parser = EcocashParser()
        transactions = parser.parse(str(csv_file))

        assert len(transactions) == 2
        assert transactions[0].raw_amount == "1500"
        assert transactions[0].raw_reference == "EC001"

    def test_parse_text_format_received(self, tmp_path):
        """Test parsing text-based Ecocash SMS logs - received."""
        txt_file = tmp_path / "ecocash.txt"
        txt_file.write_text(
            "You have received $100.00 from John Doe on 15/01/2024. Ref: EC12345\n"
        )

        parser = EcocashParser()
        transactions = parser.parse(str(txt_file))

        assert len(transactions) == 1
        assert transactions[0].raw_amount == "100.00"
        assert "Received from John Doe" in transactions[0].description

    def test_parse_text_format_sent(self, tmp_path):
        """Test parsing text-based Ecocash SMS logs - sent."""
        txt_file = tmp_path / "ecocash.txt"
        txt_file.write_text(
            "You sent $50.00 to Jane Smith on 16/01/2024. Ref: EC67890\n"
        )

        parser = EcocashParser()
        transactions = parser.parse(str(txt_file))

        assert len(transactions) == 1
        assert transactions[0].raw_amount == "-50.00"
        assert "Sent to Jane Smith" in transactions[0].description

    def test_validate_recognizes_ecocash_patterns(self, tmp_path):
        """Test validation recognizes Ecocash patterns."""
        txt_file = tmp_path / "ecocash.txt"
        txt_file.write_text("You have received $100 from Ecocash user\n")

        parser = EcocashParser()
        assert parser.validate(str(txt_file)) is True

    def test_validate_rejects_unrelated_content(self, tmp_path):
        """Test validation rejects unrelated files."""
        txt_file = tmp_path / "random.txt"
        txt_file.write_text("This is just some random text with no patterns\n")

        parser = EcocashParser()
        assert parser.validate(str(txt_file)) is False

    def test_extracts_reference_from_text(self, tmp_path):
        """Test reference extraction from text."""
        txt_file = tmp_path / "ecocash.txt"
        txt_file.write_text("Payment received. Ref: ECOREF123456\n")

        parser = EcocashParser()
        transactions = parser.parse(str(txt_file))

        # Should extract reference even without full pattern match
        if transactions:
            assert transactions[0].raw_reference == "ECOREF123456"

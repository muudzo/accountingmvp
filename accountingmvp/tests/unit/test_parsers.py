"""Unit tests for CSV parsers."""

from src.parsers import BankCSVParser, safe_filename, sanitize_csv_value


class TestSanitizer:
    """Tests for CSV sanitization functions."""

    def test_sanitize_removes_formula_prefix_equals(self):
        """Test that = prefix is neutralized."""
        result = sanitize_csv_value("=SUM(A1:A10)")
        assert result.startswith("'")
        assert "=SUM" in result

    def test_sanitize_removes_formula_prefix_plus(self):
        """Test that + prefix is neutralized."""
        result = sanitize_csv_value("+1234567890")
        assert result.startswith("'")

    def test_sanitize_removes_formula_prefix_minus(self):
        """Test that - prefix is neutralized."""
        result = sanitize_csv_value("-@cmd")
        assert result.startswith("'")

    def test_sanitize_removes_formula_prefix_at(self):
        """Test that @ prefix is neutralized."""
        result = sanitize_csv_value("@SUM(A1)")
        assert result.startswith("'")

    def test_sanitize_preserves_normal_text(self):
        """Test that normal text is unchanged."""
        result = sanitize_csv_value("Normal payment description")
        assert result == "Normal payment description"

    def test_sanitize_handles_empty_string(self):
        """Test empty string handling."""
        result = sanitize_csv_value("")
        assert result == ""

    def test_safe_filename_removes_special_chars(self):
        """Test filename sanitization."""
        result = safe_filename("../../../etc/passwd")
        assert "/" not in result
        # Path traversal should be neutralized - result shouldn't start with ..
        assert not result.startswith("..")

    def test_safe_filename_preserves_valid_chars(self):
        """Test that valid characters are preserved."""
        result = safe_filename("valid_file-name.csv")
        assert result == "valid_file-name.csv"


class TestBankCSVParser:
    """Tests for BankCSVParser."""

    def test_validate_valid_csv(self, sample_bank_csv):
        """Test validation of valid bank CSV."""
        parser = BankCSVParser()
        assert parser.validate(sample_bank_csv) is True

    def test_validate_invalid_csv(self, tmp_path):
        """Test validation of CSV with missing columns."""
        invalid_csv = tmp_path / "invalid.csv"
        invalid_csv.write_text("WrongCol1,WrongCol2\nvalue1,value2\n")

        parser = BankCSVParser()
        assert parser.validate(str(invalid_csv)) is False

    def test_parse_returns_transactions(self, sample_bank_csv):
        """Test parsing returns list of transactions."""
        parser = BankCSVParser()
        transactions = parser.parse(sample_bank_csv)

        assert len(transactions) == 4
        assert transactions[0].raw_amount == "1500.0"
        assert transactions[0].raw_reference == "TXN001"

    def test_parse_sanitizes_descriptions(self, tmp_path):
        """Test that malicious content is sanitized."""
        malicious_csv = tmp_path / "malicious.csv"
        malicious_csv.write_text(
            "Date,Reference,Amount,Description\n" "2024-01-15,REF1,100,=CMD|calc.exe\n"
        )

        parser = BankCSVParser()
        transactions = parser.parse(str(malicious_csv))

        # Should be prefixed with quote
        assert transactions[0].description.startswith("'")

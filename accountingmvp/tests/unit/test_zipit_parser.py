"""Tests for ZIPIT parser."""

import tempfile
from pathlib import Path

import pytest

from src.parsers.zipit import ZIPITParser


@pytest.fixture
def valid_zipit_content():
    """Sample valid ZIPIT file content."""
    return """# ZIPIT Transaction Export
# Generated: 2024-01-15
15/01/2024 | ZIP001 | 1500.00 | Payment from ABC Corp
16/01/2024 | ZIP002 | 250.50 | Transfer to XYZ Ltd
17-01-2024 | ZIP003 | 3000 | Invoice payment INV-123
"""


@pytest.fixture
def invalid_zipit_content():
    """Sample invalid ZIPIT file content."""
    return """Date,Reference,Amount,Description
2024-01-15,TXN001,1500.00,Payment from ABC Corp
"""


@pytest.fixture
def mixed_zipit_content():
    """ZIPIT content with some invalid lines."""
    return """15/01/2024 | ZIP001 | 1500.00 | Payment from ABC Corp
This is not a valid line
16/01/2024 | ZIP002 | 250.50 | Transfer to XYZ Ltd
Another invalid line
"""


class TestZIPITParser:
    """Test ZIPIT parser."""

    def test_validate_valid_file(self, valid_zipit_content):
        """Test validation of valid ZIPIT file."""
        parser = ZIPITParser()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(valid_zipit_content)
            temp_path = f.name

        try:
            assert parser.validate(temp_path) is True
        finally:
            Path(temp_path).unlink()

    def test_validate_invalid_file(self, invalid_zipit_content):
        """Test validation of invalid ZIPIT file."""
        parser = ZIPITParser()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(invalid_zipit_content)
            temp_path = f.name

        try:
            assert parser.validate(temp_path) is False
        finally:
            Path(temp_path).unlink()

    def test_validate_empty_file(self):
        """Test validation of empty file."""
        parser = ZIPITParser()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("")
            temp_path = f.name

        try:
            assert parser.validate(temp_path) is False
        finally:
            Path(temp_path).unlink()

    def test_validate_nonexistent_file(self):
        """Test validation of nonexistent file."""
        parser = ZIPITParser()
        assert parser.validate("/nonexistent/file.txt") is False

    def test_parse_valid_file(self, valid_zipit_content):
        """Test parsing valid ZIPIT file."""
        parser = ZIPITParser()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(valid_zipit_content)
            temp_path = f.name

        try:
            transactions = parser.parse(temp_path)

            assert len(transactions) == 3

            # Check first transaction
            assert transactions[0].raw_date == "15/01/2024"
            assert transactions[0].raw_reference == "ZIP001"
            assert transactions[0].raw_amount == "1500.00"
            assert "ABC Corp" in transactions[0].description

            # Check second transaction
            assert transactions[1].raw_date == "16/01/2024"
            assert transactions[1].raw_reference == "ZIP002"
            assert transactions[1].raw_amount == "250.50"

            # Check third transaction with different date format
            assert transactions[2].raw_date == "17-01-2024"
            assert transactions[2].raw_reference == "ZIP003"
            assert transactions[2].raw_amount == "3000"

        finally:
            Path(temp_path).unlink()

    def test_parse_with_comments(self):
        """Test parsing file with comment lines."""
        content = """# This is a comment
15/01/2024 | ZIP001 | 1500.00 | Payment
# Another comment
16/01/2024 | ZIP002 | 250.50 | Transfer
"""
        parser = ZIPITParser()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            transactions = parser.parse(temp_path)
            assert len(transactions) == 2  # Comments should be skipped
        finally:
            Path(temp_path).unlink()

    def test_parse_with_empty_lines(self):
        """Test parsing file with empty lines."""
        content = """15/01/2024 | ZIP001 | 1500.00 | Payment

16/01/2024 | ZIP002 | 250.50 | Transfer

"""
        parser = ZIPITParser()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            transactions = parser.parse(temp_path)
            assert len(transactions) == 2  # Empty lines should be skipped
        finally:
            Path(temp_path).unlink()

    def test_parse_mixed_content(self, mixed_zipit_content):
        """Test parsing file with mixed valid/invalid lines."""
        parser = ZIPITParser()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(mixed_zipit_content)
            temp_path = f.name

        try:
            transactions = parser.parse(temp_path)
            # Should only parse valid lines
            assert len(transactions) == 2
            assert transactions[0].raw_reference == "ZIP001"
            assert transactions[1].raw_reference == "ZIP002"
        finally:
            Path(temp_path).unlink()

    def test_parse_amount_with_commas(self):
        """Test parsing amounts with comma separators."""
        content = "15/01/2024 | ZIP001 | 1,500.00 | Payment\n"
        parser = ZIPITParser()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            transactions = parser.parse(temp_path)
            # Commas should be removed
            assert transactions[0].raw_amount == "1500.00"
        finally:
            Path(temp_path).unlink()

    def test_parse_sanitizes_values(self):
        """Test that CSV injection characters are sanitized."""
        content = "15/01/2024 | ZIP001 | 1500.00 | =MALICIOUS_FORMULA()\n"
        parser = ZIPITParser()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            transactions = parser.parse(temp_path)
            # Formula prefix should be removed
            assert not transactions[0].description.startswith("=")
        finally:
            Path(temp_path).unlink()

    def test_line_pattern_regex(self):
        """Test the LINE_PATTERN regex directly."""
        parser = ZIPITParser()

        # Valid patterns
        assert parser.LINE_PATTERN.match("15/01/2024 | ZIP001 | 1500.00 | Payment")
        assert parser.LINE_PATTERN.match("15-01-2024 | ABC123 | 1,500.00 | Test")

        # Invalid patterns
        assert not parser.LINE_PATTERN.match("Invalid line")
        assert not parser.LINE_PATTERN.match("15/01/2024,ZIP001,1500.00,Payment")
        assert not parser.LINE_PATTERN.match("")

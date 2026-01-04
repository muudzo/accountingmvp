"""Tests for custom exception classes."""

import pytest

from src.utils.exceptions import (
    ConfigurationError,
    FileFormatError,
    ParserError,
    ReconciliationError,
    ValidationError,
)


class TestReconciliationError:
    """Test base ReconciliationError exception."""

    def test_basic_instantiation(self):
        """Test creating basic exception."""
        error = ReconciliationError("Test error")
        assert str(error) == "Test error"

    def test_inheritance(self):
        """Test that it inherits from Exception."""
        error = ReconciliationError("Test")
        assert isinstance(error, Exception)


class TestParserError:
    """Test ParserError exception."""

    def test_with_file_and_line(self):
        """Test error with file path and line number."""
        error = ParserError("Parse failed", file_path="test.csv", line_number=42)
        assert "Parse failed" in str(error)
        assert "test.csv" in str(error)
        assert "42" in str(error)
        assert error.file_path == "test.csv"
        assert error.line_number == 42

    def test_without_file_and_line(self):
        """Test error without optional parameters."""
        error = ParserError("Parse failed")
        assert "Parse failed" in str(error)
        assert error.file_path == ""
        assert error.line_number == 0

    def test_inheritance(self):
        """Test that it inherits from ReconciliationError."""
        error = ParserError("Test")
        assert isinstance(error, ReconciliationError)


class TestValidationError:
    """Test ValidationError exception."""

    def test_with_field_and_value(self):
        """Test error with field and value."""
        error = ValidationError("Invalid amount", field="amount", value="abc")
        assert "Invalid amount" in str(error)
        assert "amount" in str(error)
        assert "abc" in str(error)
        assert error.field == "amount"
        assert error.value == "abc"

    def test_without_field_and_value(self):
        """Test error without optional parameters."""
        error = ValidationError("Invalid data")
        assert "Invalid data" in str(error)
        assert error.field == ""
        assert error.value == ""

    def test_inheritance(self):
        """Test that it inherits from ReconciliationError."""
        error = ValidationError("Test")
        assert isinstance(error, ReconciliationError)


class TestConfigurationError:
    """Test ConfigurationError exception."""

    def test_basic_instantiation(self):
        """Test creating configuration error."""
        error = ConfigurationError("Invalid config")
        assert str(error) == "Invalid config"

    def test_inheritance(self):
        """Test that it inherits from ReconciliationError."""
        error = ConfigurationError("Test")
        assert isinstance(error, ReconciliationError)


class TestFileFormatError:
    """Test FileFormatError exception."""

    def test_basic_instantiation(self):
        """Test creating file format error."""
        error = FileFormatError("Unknown format", file_path="test.txt")
        assert "Unknown format" in str(error)
        assert "test.txt" in str(error)

    def test_inheritance(self):
        """Test that it inherits from ParserError."""
        error = FileFormatError("Test")
        assert isinstance(error, ParserError)
        assert isinstance(error, ReconciliationError)

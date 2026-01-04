"""Custom exception hierarchy."""


class ReconciliationError(Exception):
    """Base exception for all reconciliation errors."""

    pass


class ParserError(ReconciliationError):
    """Raised when file parsing fails."""

    def __init__(self, message: str, file_path: str = "", line_number: int = 0):
        self.file_path = file_path
        self.line_number = line_number
        super().__init__(f"{message} (file: {file_path}, line: {line_number})")


class ValidationError(ReconciliationError):
    """Raised when data validation fails."""

    def __init__(self, message: str, field: str = "", value: str = ""):
        self.field = field
        self.value = value
        super().__init__(f"{message} (field: {field}, value: {value})")


class ConfigurationError(ReconciliationError):
    """Raised when configuration is invalid."""

    pass


class FileFormatError(ParserError):
    """Raised when file format is not recognized."""

    pass

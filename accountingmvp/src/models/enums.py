"""Enums for transaction types and statuses."""

from enum import Enum


class TransactionType(str, Enum):
    """Type of financial transaction."""

    CREDIT = "credit"
    DEBIT = "debit"
    UNKNOWN = "unknown"


class TransactionSource(str, Enum):
    """Source system for the transaction."""

    BANK_STATEMENT = "bank_statement"
    ECOCASH = "ecocash"
    ZIPIT = "zipit"
    INVOICE = "invoice"
    MANUAL = "manual"


class MatchStatus(str, Enum):
    """Status of reconciliation match."""

    MATCHED = "matched"
    UNMATCHED = "unmatched"
    PARTIAL = "partial"
    MANUAL_REVIEW = "manual_review"


class MatchConfidence(str, Enum):
    """Confidence level for a match."""

    HIGH = "high"  # >= 90%
    MEDIUM = "medium"  # 70-89%
    LOW = "low"  # 50-69%
    NONE = "none"  # < 50%

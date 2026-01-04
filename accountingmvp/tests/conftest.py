"""Pytest configuration and fixtures."""

from datetime import date
from decimal import Decimal

import pytest

from src.models.transaction import NormalizedTransaction, RawTransaction


@pytest.fixture
def sample_bank_csv_content():
    """Sample bank statement CSV content."""
    return """Date,Reference,Amount,Description
2024-01-15,TXN001,1500.00,Payment from ABC Corp
2024-01-16,TXN002,-250.50,Transfer to XYZ Ltd
2024-01-17,TXN003,750.00,Invoice INV-2024-001
2024-01-18,TXN004,100.00,Refund from Supplier A
"""


@pytest.fixture
def sample_ecocash_csv_content():
    """Sample Ecocash export content."""
    return """Date,Reference,Amount,Description
15/01/2024,EC001,1500,ABC Corporation payment
16/01/2024,EC002,250,XYZ Limited transfer
17/01/2024,EC003,750,INV-2024-001 settlement
"""


@pytest.fixture
def sample_bank_csv(sample_bank_csv_content, tmp_path):
    """Create temporary bank CSV file."""
    file_path = tmp_path / "bank_statement.csv"
    file_path.write_text(sample_bank_csv_content)
    return str(file_path)


@pytest.fixture
def sample_ecocash_csv(sample_ecocash_csv_content, tmp_path):
    """Create temporary Ecocash CSV file."""
    file_path = tmp_path / "ecocash_export.csv"
    file_path.write_text(sample_ecocash_csv_content)
    return str(file_path)


@pytest.fixture
def raw_transaction():
    """Sample raw transaction."""
    return RawTransaction(
        raw_date="2024-01-15",
        raw_amount="1500.00",
        raw_reference="TXN001",
        description="Payment from ABC Corp",
        source_file="test.csv",
        line_number=2,
    )


@pytest.fixture
def normalized_transaction():
    """Sample normalized transaction."""
    return NormalizedTransaction(
        id="abc123def456",
        transaction_date=date(2024, 1, 15),
        amount=Decimal("1500.00"),
        reference="TXN001",
        description="Payment from ABC Corp",
        source="bank_statement",
    )


@pytest.fixture
def matching_normalized_transaction():
    """Transaction that should match with normalized_transaction."""
    return NormalizedTransaction(
        id="xyz789ghi012",
        transaction_date=date(2024, 1, 15),
        amount=Decimal("1500.00"),
        reference="EC001",
        description="ABC Corporation payment",
        source="ecocash",
    )


@pytest.fixture
def non_matching_transaction():
    """Transaction that should not match."""
    return NormalizedTransaction(
        id="nomatch12345",
        transaction_date=date(2024, 2, 20),
        amount=Decimal("9999.99"),
        reference="DIFF001",
        description="Completely different transaction",
        source="ecocash",
    )

from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

class RawTransaction(BaseModel):
    """Represents a transaction row exactly as parsed from CSV."""
    raw_date: str
    raw_amount: str
    raw_reference: str
    description: str
    source_file: str
    line_number: int

class NormalizedTransaction(BaseModel):
    """Standardized transaction schema for the ledger."""
    model_config = ConfigDict(frozen=True)

    id: str = Field(..., description="Unique hash of the transaction")
    transaction_date: date
    amount: Decimal
    reference: str
    description: str
    source: str
    currency: str = "USD"
    metadata: dict = Field(default_factory=dict)

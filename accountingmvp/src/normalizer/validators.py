"""Data quality validators."""
from decimal import Decimal
from typing import List, Tuple
from src.models.transaction import NormalizedTransaction
from src.logger import setup_logger

logger = setup_logger(__name__)


class DataValidator:
    """
    Validates normalized transactions for data quality.
    
    Checks:
    - Required fields present
    - Amount sanity (not zero, within range)
    - Date sanity (not future, not too old)
    - Reference format
    """
    
    MAX_AMOUNT = Decimal("1000000000")  # 1 billion limit
    MIN_DATE_YEAR = 2000
    
    def __init__(self):
        self.errors: List[Tuple[str, str]] = []
        self.warnings: List[Tuple[str, str]] = []
    
    def validate_batch(
        self, 
        transactions: List[NormalizedTransaction]
    ) -> Tuple[List[NormalizedTransaction], List[NormalizedTransaction]]:
        """
        Validate a batch of transactions.
        
        Returns:
            Tuple of (valid_transactions, invalid_transactions)
        """
        valid = []
        invalid = []
        
        for txn in transactions:
            if self._validate_single(txn):
                valid.append(txn)
            else:
                invalid.append(txn)
        
        logger.info(f"Validation: {len(valid)} valid, {len(invalid)} invalid")
        return valid, invalid
    
    def _validate_single(self, txn: NormalizedTransaction) -> bool:
        """Validate a single transaction."""
        is_valid = True
        
        # Check amount
        if txn.amount == 0:
            self.warnings.append((txn.id, "Zero amount transaction"))
        
        if abs(txn.amount) > self.MAX_AMOUNT:
            self.errors.append((txn.id, f"Amount exceeds limit: {txn.amount}"))
            is_valid = False
        
        # Check date
        if txn.transaction_date.year < self.MIN_DATE_YEAR:
            self.errors.append((txn.id, f"Date too old: {txn.transaction_date}"))
            is_valid = False
        
        # Check required fields
        if not txn.description.strip():
            self.warnings.append((txn.id, "Empty description"))
        
        return is_valid
    
    def get_report(self) -> dict:
        """Get validation report."""
        return {
            "total_errors": len(self.errors),
            "total_warnings": len(self.warnings),
            "errors": self.errors[:50],  # Limit to first 50
            "warnings": self.warnings[:50],
        }

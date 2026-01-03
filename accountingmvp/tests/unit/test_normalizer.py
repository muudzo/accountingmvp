"""Unit tests for normalization pipeline."""
import pytest
from decimal import Decimal
from datetime import date

from src.normalizer import NormalizationPipeline, DataValidator
from src.models.transaction import RawTransaction, NormalizedTransaction
from src.models.enums import TransactionSource


class TestNormalizationPipeline:
    """Tests for NormalizationPipeline."""
    
    def test_normalizes_raw_transaction(self):
        """Test basic normalization of a raw transaction."""
        pipeline = NormalizationPipeline(TransactionSource.BANK_STATEMENT)
        
        raw = RawTransaction(
            raw_date="2024-01-15",
            raw_amount="1500.00",
            raw_reference="TXN001",
            description="Payment from ABC Corp",
            source_file="bank.csv",
            line_number=2
        )
        
        result = pipeline.process([raw])
        
        assert len(result) == 1
        assert result[0].transaction_date == date(2024, 1, 15)
        assert result[0].amount == Decimal("1500.00")
        assert result[0].reference == "TXN001"
    
    def test_handles_various_date_formats(self):
        """Test parsing of various date formats."""
        pipeline = NormalizationPipeline(TransactionSource.BANK_STATEMENT)
        
        raw_transactions = [
            RawTransaction(
                raw_date="15/01/2024", raw_amount="100",
                raw_reference="R1", description="Test",
                source_file="test.csv", line_number=1
            ),
            RawTransaction(
                raw_date="2024-01-16", raw_amount="200",
                raw_reference="R2", description="Test",
                source_file="test.csv", line_number=2
            ),
            RawTransaction(
                raw_date="17 Jan 2024", raw_amount="300",
                raw_reference="R3", description="Test",
                source_file="test.csv", line_number=3
            ),
        ]
        
        result = pipeline.process(raw_transactions)
        
        assert len(result) == 3
        assert result[0].transaction_date == date(2024, 1, 15)
        assert result[1].transaction_date == date(2024, 1, 16)
        assert result[2].transaction_date == date(2024, 1, 17)
    
    def test_handles_amount_formats(self):
        """Test parsing of various amount formats."""
        pipeline = NormalizationPipeline(TransactionSource.BANK_STATEMENT)
        
        raw_transactions = [
            RawTransaction(
                raw_date="2024-01-15", raw_amount="$1,500.00",
                raw_reference="R1", description="Test",
                source_file="test.csv", line_number=1
            ),
            RawTransaction(
                raw_date="2024-01-15", raw_amount="(500.00)",
                raw_reference="R2", description="Test",
                source_file="test.csv", line_number=2
            ),
        ]
        
        result = pipeline.process(raw_transactions)
        
        assert len(result) == 2
        assert result[0].amount == Decimal("1500.00")
        assert result[1].amount == Decimal("-500.00")
    
    def test_deduplicates_transactions(self):
        """Test that duplicate transactions are removed."""
        pipeline = NormalizationPipeline(TransactionSource.BANK_STATEMENT)
        
        raw = RawTransaction(
            raw_date="2024-01-15", raw_amount="1000",
            raw_reference="DUP", description="Same transaction",
            source_file="test.csv", line_number=1
        )
        
        # Process same transaction twice
        result = pipeline.process([raw, raw])
        
        assert len(result) == 1
    
    def test_skips_invalid_dates(self):
        """Test that transactions with invalid dates are skipped."""
        pipeline = NormalizationPipeline(TransactionSource.BANK_STATEMENT)
        
        raw = RawTransaction(
            raw_date="not-a-date", raw_amount="100",
            raw_reference="R1", description="Test",
            source_file="test.csv", line_number=1
        )
        
        result = pipeline.process([raw])
        
        assert len(result) == 0


class TestDataValidator:
    """Tests for DataValidator."""
    
    def test_validates_normal_transaction(self):
        """Test that normal transactions pass validation."""
        validator = DataValidator()
        
        txn = NormalizedTransaction(
            id="test123",
            transaction_date=date(2024, 1, 15),
            amount=Decimal("1000.00"),
            reference="REF001",
            description="Normal payment",
            source="bank_statement"
        )
        
        valid, invalid = validator.validate_batch([txn])
        
        assert len(valid) == 1
        assert len(invalid) == 0
    
    def test_rejects_extremely_large_amounts(self):
        """Test that extremely large amounts are rejected."""
        validator = DataValidator()
        
        txn = NormalizedTransaction(
            id="test123",
            transaction_date=date(2024, 1, 15),
            amount=Decimal("9999999999999"),  # Over 1 billion
            reference="REF001",
            description="Huge amount",
            source="bank_statement"
        )
        
        valid, invalid = validator.validate_batch([txn])
        
        assert len(valid) == 0
        assert len(invalid) == 1
    
    def test_rejects_very_old_dates(self):
        """Test that very old dates are rejected."""
        validator = DataValidator()
        
        txn = NormalizedTransaction(
            id="test123",
            transaction_date=date(1990, 1, 15),  # Before 2000
            amount=Decimal("100"),
            reference="REF001",
            description="Old transaction",
            source="bank_statement"
        )
        
        valid, invalid = validator.validate_batch([txn])
        
        assert len(valid) == 0
        assert len(invalid) == 1
    
    def test_generates_warning_for_zero_amount(self):
        """Test that zero amounts generate warnings but pass."""
        validator = DataValidator()
        
        txn = NormalizedTransaction(
            id="test123",
            transaction_date=date(2024, 1, 15),
            amount=Decimal("0"),
            reference="REF001",
            description="Zero amount",
            source="bank_statement"
        )
        
        valid, invalid = validator.validate_batch([txn])
        
        # Should pass but generate warning
        assert len(valid) == 1
        report = validator.get_report()
        assert report["total_warnings"] > 0

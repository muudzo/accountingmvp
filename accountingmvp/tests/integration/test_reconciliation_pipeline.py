"""Integration tests for the full reconciliation pipeline."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.models.enums import MatchStatus, TransactionSource
from src.normalizer import NormalizationPipeline
from src.parsers import BankCSVParser
from src.reconciliation import ReconciliationEngine


class TestReconciliationPipeline:
    """End-to-end tests for the reconciliation pipeline."""

    def test_full_pipeline_with_sample_data(self, sample_bank_csv, sample_ecocash_csv):
        """Test complete pipeline from CSV to reconciliation results."""
        # Parse bank statement
        bank_parser = BankCSVParser()
        bank_raw = bank_parser.parse(sample_bank_csv)

        # Parse Ecocash
        ecocash_parser = BankCSVParser()  # Using same format for test
        ecocash_raw = ecocash_parser.parse(sample_ecocash_csv)

        # Normalize
        bank_pipeline = NormalizationPipeline(TransactionSource.BANK_STATEMENT)
        bank_normalized = bank_pipeline.process(bank_raw)

        ecocash_pipeline = NormalizationPipeline(TransactionSource.ECOCASH)
        ecocash_normalized = ecocash_pipeline.process(ecocash_raw)

        # Reconcile
        engine = ReconciliationEngine(confidence_threshold=0.70)
        matches, summary = engine.reconcile(bank_normalized, ecocash_normalized)

        # Assertions
        assert len(matches) > 0
        assert summary.total_source_transactions == 4
        assert summary.total_target_transactions == 3
        assert summary.match_rate > 0

    def test_exact_reference_matching(self, tmp_path):
        """Test that exact reference matches are found."""
        # Create CSV with matching references
        source_csv = tmp_path / "source.csv"
        source_csv.write_text(
            "Date,Reference,Amount,Description\n"
            "2024-01-15,EXACT-REF-001,1000.00,Test payment\n"
        )

        target_csv = tmp_path / "target.csv"
        target_csv.write_text(
            "Date,Reference,Amount,Description\n"
            "2024-01-15,EXACT-REF-001,1000.00,Test payment received\n"
        )

        # Parse and normalize
        parser = BankCSVParser()

        source_raw = parser.parse(str(source_csv))
        target_raw = parser.parse(str(target_csv))

        source_pipeline = NormalizationPipeline(TransactionSource.BANK_STATEMENT)
        target_pipeline = NormalizationPipeline(TransactionSource.ECOCASH)

        source_norm = source_pipeline.process(source_raw)
        target_norm = target_pipeline.process(target_raw)

        # Reconcile
        engine = ReconciliationEngine()
        matches, summary = engine.reconcile(source_norm, target_norm)

        # Should find exact match
        matched = [m for m in matches if m.status == MatchStatus.MATCHED]
        assert len(matched) == 1
        assert matched[0].matched_by == "exact_reference"

    def test_no_matches_for_different_data(self, tmp_path):
        """Test that unrelated data produces no matches."""
        source_csv = tmp_path / "source.csv"
        source_csv.write_text(
            "Date,Reference,Amount,Description\n" "2024-01-15,REF-A,1000.00,Payment A\n"
        )

        target_csv = tmp_path / "target.csv"
        target_csv.write_text(
            "Date,Reference,Amount,Description\n"
            "2024-06-30,REF-Z,9999.00,Completely different\n"
        )

        parser = BankCSVParser()

        source_norm = NormalizationPipeline(TransactionSource.BANK_STATEMENT).process(
            parser.parse(str(source_csv))
        )
        target_norm = NormalizationPipeline(TransactionSource.ECOCASH).process(
            parser.parse(str(target_csv))
        )

        engine = ReconciliationEngine()
        matches, summary = engine.reconcile(source_norm, target_norm)

        # Should find no matches
        matched = [m for m in matches if m.status == MatchStatus.MATCHED]
        assert len(matched) == 0
        assert summary.unmatched_source_count == 1

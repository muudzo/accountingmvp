"""Tests for report generation."""

import tempfile
from datetime import datetime
from decimal import Decimal
from pathlib import Path

import pytest

from src.models.enums import MatchStatus, TransactionSource
from src.models.match import MatchResult, MatchScore, ReconciliationSummary
from src.models.transaction import NormalizedTransaction
from src.reconciliation.reporter import ReportGenerator


@pytest.fixture
def sample_transactions():
    """Create sample transactions for testing."""
    source = NormalizedTransaction(
        id="src1",
        transaction_date=datetime(2024, 1, 15).date(),
        amount=Decimal("1500.00"),
        reference="TXN001",
        description="Payment from ABC Corp",
        source=TransactionSource.BANK_STATEMENT.value,
    )

    target = NormalizedTransaction(
        id="tgt1",
        transaction_date=datetime(2024, 1, 15).date(),
        amount=Decimal("1500.00"),
        reference="INV001",
        description="ABC Corporation payment",
        source=TransactionSource.ECOCASH.value,
    )

    return source, target



@pytest.fixture
def sample_match_result(sample_transactions):
    """Create a sample match result."""
    source, target = sample_transactions
    score = MatchScore(
        amount_score=1.0,
        text_score=0.85,
        date_score=1.0,
        reference_bonus=0.0,
    )

    return MatchResult(
        source_transaction=source,
        target_transaction=target,
        score=score,
        status=MatchStatus.MATCHED,
        matched_by="fuzzy_text",
    )


@pytest.fixture
def sample_summary():
    """Create a sample reconciliation summary."""
    return ReconciliationSummary(
        total_source_transactions=10,
        total_target_transactions=10,
        matched_count=8,
        unmatched_source_count=2,
        unmatched_target_count=2,
        manual_review_count=1,
        match_rate=0.8,
        total_matched_amount=Decimal("12000.00"),
        total_unmatched_amount=Decimal("3000.00"),
    )


class TestReportGenerator:
    """Test ReportGenerator class."""

    def test_initialization(self):
        """Test reporter initialization."""
        reporter = ReportGenerator()
        assert reporter.generated_at is not None
        assert isinstance(reporter.generated_at, datetime)

    def test_generate_csv(self, sample_match_result):
        """Test CSV generation."""
        reporter = ReportGenerator()
        csv_data = reporter.generate_csv([sample_match_result])

        assert isinstance(csv_data, str)
        assert "Source Date" in csv_data
        assert "Source Amount" in csv_data
        assert "Target Date" in csv_data
        assert "Confidence" in csv_data
        assert "TXN001" in csv_data
        assert "INV001" in csv_data

    def test_generate_csv_bytes(self, sample_match_result):
        """Test CSV bytes generation."""
        reporter = ReportGenerator()
        csv_bytes = reporter.generate_csv_bytes([sample_match_result])

        assert isinstance(csv_bytes, bytes)
        assert b"Source Date" in csv_bytes
        assert b"TXN001" in csv_bytes



    def test_generate_excel(self, sample_match_result, sample_summary):
        """Test Excel generation."""
        reporter = ReportGenerator()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = str(Path(tmpdir) / "test_report.xlsx")
            result_path = reporter.generate_excel(
                [sample_match_result], sample_summary, output_path
            )

            assert result_path == output_path
            assert Path(output_path).exists()
            assert Path(output_path).stat().st_size > 0

    def test_summary_to_df(self, sample_summary):
        """Test summary to DataFrame conversion."""
        reporter = ReportGenerator()
        df = reporter._summary_to_df(sample_summary)

        assert len(df) == 10  # 10 metrics
        assert "Metric" in df.columns
        assert "Value" in df.columns
        assert "Total Source Transactions" in df["Metric"].values
        assert "Match Rate" in df["Metric"].values

    def test_matches_to_df(self, sample_match_result):
        """Test matches to DataFrame conversion."""
        reporter = ReportGenerator()
        df = reporter._matches_to_df([sample_match_result])

        assert len(df) == 1
        assert "Source Date" in df.columns
        assert "Target Amount" in df.columns
        assert "Confidence" in df.columns
        assert df.iloc[0]["Source Reference"] == "TXN001"
        assert df.iloc[0]["Target Reference"] == "INV001"

    def test_matches_to_df_multiple_statuses(self, sample_transactions):
        """Test DataFrame with different match statuses."""
        source, target = sample_transactions
        score = MatchScore(
            amount_score=0.7,
            text_score=0.6,
            date_score=0.8,
            reference_bonus=0.0,
        )

        matches = [
            MatchResult(
                source_transaction=source,
                target_transaction=target,
                score=score,
                status=MatchStatus.MATCHED,
                matched_by="amount",
            ),
            MatchResult(
                source_transaction=source,
                target_transaction=target,
                score=score,
                status=MatchStatus.MANUAL_REVIEW,
                matched_by="fuzzy_text",
            ),
            MatchResult(
                source_transaction=source,
                target_transaction=target,
                score=score,
                status=MatchStatus.UNMATCHED,
                matched_by="none",
            ),
        ]

        reporter = ReportGenerator()
        df = reporter._matches_to_df(matches)

        assert len(df) == 3
        assert df["Status"].tolist() == ["matched", "manual_review", "unmatched"]



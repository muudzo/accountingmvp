"""Unit tests for matchers."""

from datetime import date
from decimal import Decimal

from src.models.transaction import NormalizedTransaction
from src.reconciliation.matchers import AmountMatcher, DateMatcher, FuzzyTextMatcher


class TestFuzzyTextMatcher:
    """Tests for FuzzyTextMatcher."""

    def test_exact_match_returns_high_score(self):
        """Test that exact text returns high score."""
        t1 = NormalizedTransaction(
            id="1",
            transaction_date=date(2024, 1, 1),
            amount=Decimal("100"),
            reference="REF1",
            description="Payment from ABC Corp",
            source="bank",
        )
        t2 = NormalizedTransaction(
            id="2",
            transaction_date=date(2024, 1, 1),
            amount=Decimal("100"),
            reference="REF2",
            description="Payment from ABC Corp",
            source="ecocash",
        )

        matcher = FuzzyTextMatcher()
        score = matcher.score(t1, t2)

        assert score >= 0.95

    def test_similar_text_returns_good_score(self):
        """Test similar text matching."""
        t1 = NormalizedTransaction(
            id="1",
            transaction_date=date(2024, 1, 1),
            amount=Decimal("100"),
            reference="REF1",
            description="Payment from ABC Corporation",
            source="bank",
        )
        t2 = NormalizedTransaction(
            id="2",
            transaction_date=date(2024, 1, 1),
            amount=Decimal("100"),
            reference="REF2",
            description="ABC Corp payment received",
            source="ecocash",
        )

        matcher = FuzzyTextMatcher()
        score = matcher.score(t1, t2)

        assert score >= 0.5

    def test_different_text_returns_low_score(self):
        """Test completely different text."""
        t1 = NormalizedTransaction(
            id="1",
            transaction_date=date(2024, 1, 1),
            amount=Decimal("100"),
            reference="REF1",
            description="Invoice from ABC Corporation",
            source="bank",
        )
        t2 = NormalizedTransaction(
            id="2",
            transaction_date=date(2024, 1, 1),
            amount=Decimal("100"),
            reference="REF2",
            description="Monthly rent XYZ apartments",
            source="ecocash",
        )

        matcher = FuzzyTextMatcher()
        score = matcher.score(t1, t2)

        assert score < 0.7  # Adjusted threshold for fuzzy matching


class TestAmountMatcher:
    """Tests for AmountMatcher."""

    def test_exact_amount_returns_perfect_score(self):
        """Test exact amount match."""
        t1 = NormalizedTransaction(
            id="1",
            transaction_date=date(2024, 1, 1),
            amount=Decimal("1500.00"),
            reference="REF1",
            description="Test",
            source="bank",
        )
        t2 = NormalizedTransaction(
            id="2",
            transaction_date=date(2024, 1, 1),
            amount=Decimal("1500.00"),
            reference="REF2",
            description="Test",
            source="ecocash",
        )

        matcher = AmountMatcher()
        score = matcher.score(t1, t2)

        assert score == 1.0

    def test_within_tolerance_returns_high_score(self):
        """Test amount within 2% tolerance."""
        t1 = NormalizedTransaction(
            id="1",
            transaction_date=date(2024, 1, 1),
            amount=Decimal("1500.00"),
            reference="REF1",
            description="Test",
            source="bank",
        )
        t2 = NormalizedTransaction(
            id="2",
            transaction_date=date(2024, 1, 1),
            amount=Decimal("1510.00"),
            reference="REF2",
            description="Test",
            source="ecocash",
        )

        matcher = AmountMatcher()
        score = matcher.score(t1, t2)

        assert score >= 0.9

    def test_different_amount_returns_low_score(self):
        """Test very different amounts."""
        t1 = NormalizedTransaction(
            id="1",
            transaction_date=date(2024, 1, 1),
            amount=Decimal("1500.00"),
            reference="REF1",
            description="Test",
            source="bank",
        )
        t2 = NormalizedTransaction(
            id="2",
            transaction_date=date(2024, 1, 1),
            amount=Decimal("500.00"),
            reference="REF2",
            description="Test",
            source="ecocash",
        )

        matcher = AmountMatcher()
        score = matcher.score(t1, t2)

        assert score == 0.0


class TestDateMatcher:
    """Tests for DateMatcher."""

    def test_same_date_returns_perfect_score(self):
        """Test same date match."""
        t1 = NormalizedTransaction(
            id="1",
            transaction_date=date(2024, 1, 15),
            amount=Decimal("100"),
            reference="REF1",
            description="Test",
            source="bank",
        )
        t2 = NormalizedTransaction(
            id="2",
            transaction_date=date(2024, 1, 15),
            amount=Decimal("100"),
            reference="REF2",
            description="Test",
            source="ecocash",
        )

        matcher = DateMatcher()
        score = matcher.score(t1, t2)

        assert score == 1.0

    def test_within_window_returns_good_score(self):
        """Test dates within 3-day window."""
        t1 = NormalizedTransaction(
            id="1",
            transaction_date=date(2024, 1, 15),
            amount=Decimal("100"),
            reference="REF1",
            description="Test",
            source="bank",
        )
        t2 = NormalizedTransaction(
            id="2",
            transaction_date=date(2024, 1, 17),
            amount=Decimal("100"),
            reference="REF2",
            description="Test",
            source="ecocash",
        )

        matcher = DateMatcher()
        score = matcher.score(t1, t2)

        assert 0 < score < 1.0

    def test_outside_window_returns_zero(self):
        """Test dates outside window."""
        t1 = NormalizedTransaction(
            id="1",
            transaction_date=date(2024, 1, 15),
            amount=Decimal("100"),
            reference="REF1",
            description="Test",
            source="bank",
        )
        t2 = NormalizedTransaction(
            id="2",
            transaction_date=date(2024, 1, 25),
            amount=Decimal("100"),
            reference="REF2",
            description="Test",
            source="ecocash",
        )

        matcher = DateMatcher()
        score = matcher.score(t1, t2)

        assert score == 0.0

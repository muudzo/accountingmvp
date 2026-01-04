"""Confidence scoring for reconciliation matches."""

from src.models.match import MatchConfidence, MatchScore
from src.models.transaction import NormalizedTransaction

from .matchers import AmountMatcher, DateMatcher, FuzzyTextMatcher


class ConfidenceScorer:
    """
    Calculates confidence scores for transaction matches.

    Combines multiple signals:
    - Amount similarity (40%)
    - Text similarity (30%)
    - Date proximity (20%)
    - Reference match bonus (10%)
    """

    # Weights for scoring components
    WEIGHT_AMOUNT = 0.40
    WEIGHT_TEXT = 0.30
    WEIGHT_DATE = 0.20
    WEIGHT_REF_BONUS = 0.10

    def __init__(self):
        self.text_matcher = FuzzyTextMatcher()
        self.amount_matcher = AmountMatcher()
        self.date_matcher = DateMatcher()

    def calculate_score(
        self, source: NormalizedTransaction, target: NormalizedTransaction
    ) -> MatchScore:
        """
        Calculate detailed match score between two transactions.

        Args:
            source: Source transaction (e.g., bank statement)
            target: Target transaction (e.g., invoice)

        Returns:
            MatchScore with breakdown
        """
        amount_score = self.amount_matcher.score(source, target)
        text_score = self.text_matcher.score(source, target)
        date_score = self.date_matcher.score(source, target)

        # Reference bonus for exact match
        ref_bonus = 0.1 if self._exact_reference_match(source, target) else 0.0

        return MatchScore(
            amount_score=amount_score,
            text_score=text_score,
            date_score=date_score,
            reference_bonus=ref_bonus,
        )

    def _exact_reference_match(
        self, t1: NormalizedTransaction, t2: NormalizedTransaction
    ) -> bool:
        """Check for exact reference match."""
        ref1 = t1.reference.strip().upper()
        ref2 = t2.reference.strip().upper()
        return ref1 and ref2 and ref1 == ref2

    def get_confidence_level(self, score: MatchScore) -> MatchConfidence:
        """Get confidence level from score."""
        return score.confidence

    def should_manual_review(self, score: MatchScore) -> bool:
        """Check if match needs manual review."""
        return score.confidence in (MatchConfidence.LOW, MatchConfidence.MEDIUM)

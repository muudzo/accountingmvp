"""Amount matching with tolerance."""

from decimal import Decimal

from src.models.transaction import NormalizedTransaction


class AmountMatcher:
    """
    Matches transactions by amount with configurable tolerance.

    Handles:
    - Exact matches
    - Percentage-based tolerance
    - Absolute tolerance
    - Sign considerations (debit/credit)
    """

    def __init__(
        self,
        percentage_tolerance: float = 0.02,  # 2%
        absolute_tolerance: Decimal = Decimal("0.01"),
    ):
        """
        Initialize matcher.

        Args:
            percentage_tolerance: Max percentage difference (0.02 = 2%)
            absolute_tolerance: Max absolute difference for small amounts
        """
        self.percentage_tolerance = percentage_tolerance
        self.absolute_tolerance = absolute_tolerance

    def score(self, txn1: NormalizedTransaction, txn2: NormalizedTransaction) -> float:
        """
        Calculate amount similarity score.

        Returns:
            Score from 0 to 1 (1 = exact match)
        """
        amt1 = abs(txn1.amount)
        amt2 = abs(txn2.amount)

        if amt1 == amt2:
            return 1.0

        if amt1 == 0 or amt2 == 0:
            return 0.0

        # Calculate percentage difference
        diff = abs(amt1 - amt2)
        avg = (amt1 + amt2) / 2
        pct_diff = float(diff / avg)

        # Perfect score if within tolerance
        if pct_diff <= self.percentage_tolerance:
            # Score decreases as difference increases
            return 1.0 - (pct_diff / self.percentage_tolerance) * 0.1

        # Check absolute tolerance for small amounts
        if diff <= self.absolute_tolerance:
            return 0.95

        # Score falls off gradually
        if pct_diff < 0.10:  # Within 10%
            return max(0.5, 1.0 - pct_diff)

        return 0.0

    def is_match(
        self, txn1: NormalizedTransaction, txn2: NormalizedTransaction
    ) -> bool:
        """Check if amounts match within tolerance."""
        return self.score(txn1, txn2) >= 0.9

    def get_amount_diff(
        self, txn1: NormalizedTransaction, txn2: NormalizedTransaction
    ) -> Decimal:
        """Get absolute difference between amounts."""
        return abs(txn1.amount - txn2.amount)

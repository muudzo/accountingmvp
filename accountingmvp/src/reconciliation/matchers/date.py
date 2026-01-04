"""Date proximity matching."""

from datetime import date, timedelta

from src.models.transaction import NormalizedTransaction


class DateMatcher:
    """
    Matches transactions by date proximity.

    Handles:
    - Exact date matches
    - Configurable window (e.g., ±3 days)
    - Decay scoring based on distance
    """

    def __init__(self, window_days: int = 3):
        """
        Initialize matcher.

        Args:
            window_days: Maximum days difference to consider a match
        """
        self.window_days = window_days

    def score(self, txn1: NormalizedTransaction, txn2: NormalizedTransaction) -> float:
        """
        Calculate date proximity score.

        Returns:
            Score from 0 to 1 (1 = same day)
        """
        days_diff = abs((txn1.transaction_date - txn2.transaction_date).days)

        if days_diff == 0:
            return 1.0

        if days_diff > self.window_days:
            return 0.0

        # Linear decay within window
        return 1.0 - (days_diff / (self.window_days + 1))

    def is_match(
        self, txn1: NormalizedTransaction, txn2: NormalizedTransaction
    ) -> bool:
        """Check if dates are within window."""
        days_diff = abs((txn1.transaction_date - txn2.transaction_date).days)
        return days_diff <= self.window_days

    def get_date_range(self, txn: NormalizedTransaction) -> tuple[date, date]:
        """Get the date window for a transaction."""
        start = txn.transaction_date - timedelta(days=self.window_days)
        end = txn.transaction_date + timedelta(days=self.window_days)
        return start, end

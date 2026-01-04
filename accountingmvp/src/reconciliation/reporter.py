"""Reconciliation report generator."""

from datetime import datetime

import pandas as pd

from src.models.enums import MatchStatus
from src.models.match import MatchResult, ReconciliationSummary


class ReportGenerator:
    """
    Generates reconciliation reports in various formats.

    Supported formats:
    - Excel (.xlsx)
    - CSV
    - Summary DataFrame
    """

    def __init__(self):
        self.generated_at = datetime.now()

    def generate_excel(
        self,
        matches: list[MatchResult],
        summary: ReconciliationSummary,
        output_path: str,
    ) -> str:
        """
        Generate Excel report with multiple sheets.

        Args:
            matches: List of match results
            summary: Reconciliation summary
            output_path: Path to save Excel file

        Returns:
            Path to generated file
        """
        with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
            # Summary sheet
            summary_df = self._summary_to_df(summary)
            summary_df.to_excel(writer, sheet_name="Summary", index=False)

            # Matched transactions
            matched = [m for m in matches if m.status == MatchStatus.MATCHED]
            if matched:
                matched_df = self._matches_to_df(matched)
                matched_df.to_excel(writer, sheet_name="Matched", index=False)

            # Manual review
            review = [m for m in matches if m.status == MatchStatus.MANUAL_REVIEW]
            if review:
                review_df = self._matches_to_df(review)
                review_df.to_excel(writer, sheet_name="Manual Review", index=False)

            # Unmatched
            unmatched = [m for m in matches if m.status == MatchStatus.UNMATCHED]
            if unmatched:
                unmatched_df = self._matches_to_df(unmatched)
                unmatched_df.to_excel(writer, sheet_name="Unmatched", index=False)

        return output_path

    def generate_csv(self, matches: list[MatchResult]) -> str:
        """Generate CSV string of all matches."""
        df = self._matches_to_df(matches)
        return df.to_csv(index=False)

    def generate_csv_bytes(self, matches: list[MatchResult]) -> bytes:
        """Generate CSV as bytes for download."""
        return self.generate_csv(matches).encode("utf-8")

    def _summary_to_df(self, summary: ReconciliationSummary) -> pd.DataFrame:
        """Convert summary to DataFrame."""
        data = {
            "Metric": [
                "Total Source Transactions",
                "Total Target Transactions",
                "Matched Count",
                "Unmatched Source Count",
                "Unmatched Target Count",
                "Manual Review Count",
                "Match Rate",
                "Total Matched Amount",
                "Total Unmatched Amount",
                "Report Generated",
            ],
            "Value": [
                summary.total_source_transactions,
                summary.total_target_transactions,
                summary.matched_count,
                summary.unmatched_source_count,
                summary.unmatched_target_count,
                summary.manual_review_count,
                f"{summary.match_rate:.1%}",
                f"${summary.total_matched_amount:,.2f}",
                f"${summary.total_unmatched_amount:,.2f}",
                self.generated_at.strftime("%Y-%m-%d %H:%M:%S"),
            ],
        }
        return pd.DataFrame(data)

    def _matches_to_df(self, matches: list[MatchResult]) -> pd.DataFrame:
        """Convert matches to DataFrame."""
        rows = []
        for m in matches:
            rows.append(
                {
                    "Source Date": m.source_transaction.transaction_date,
                    "Source Amount": float(m.source_transaction.amount),
                    "Source Reference": m.source_transaction.reference,
                    "Source Description": m.source_transaction.description[:50],
                    "Target Date": m.target_transaction.transaction_date,
                    "Target Amount": float(m.target_transaction.amount),
                    "Target Reference": m.target_transaction.reference,
                    "Target Description": m.target_transaction.description[:50],
                    "Confidence": f"{m.score.total_score:.0%}",
                    "Status": m.status.value,
                    "Matched By": m.matched_by,
                }
            )
        return pd.DataFrame(rows)

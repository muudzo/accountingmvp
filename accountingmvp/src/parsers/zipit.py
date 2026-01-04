"""ZIPIT text file parser."""

import re

from src.models.transaction import RawTransaction

from .base import BaseParser
from .sanitizer import sanitize_csv_value


class ZIPITParser(BaseParser):
    """
    Parser for ZIPIT text file exports.

    ZIPIT files are typically line-based with a specific format:
    DATE | REFERENCE | AMOUNT | DESCRIPTION
    """

    # Regex pattern for ZIPIT line format
    LINE_PATTERN = re.compile(
        r"^(\d{2}[/-]\d{2}[/-]\d{4})\s*\|\s*([A-Z0-9]+)\s*\|\s*([\d,.-]+)\s*\|\s*(.+)$"
    )

    def validate(self, file_path: str) -> bool:
        """Check if file matches ZIPIT format."""
        try:
            with open(file_path, encoding="utf-8") as f:
                # Check first few non-empty lines
                valid_lines = 0
                for i, line in enumerate(f):
                    if i > 10:
                        break
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if self.LINE_PATTERN.match(line):
                        valid_lines += 1
                return valid_lines >= 2
        except Exception:
            return False

    def parse(self, file_path: str) -> list[RawTransaction]:
        """Parse ZIPIT text file into raw transactions."""
        transactions = []

        with open(file_path, encoding="utf-8", errors="replace") as f:
            for line_num, line in enumerate(f, start=1):
                line = line.strip()

                # Skip empty lines and comments
                if not line or line.startswith("#"):
                    continue

                match = self.LINE_PATTERN.match(line)
                if match:
                    date_str, ref, amount, desc = match.groups()

                    txn = RawTransaction(
                        raw_date=date_str,
                        raw_amount=amount.replace(",", ""),
                        raw_reference=sanitize_csv_value(ref),
                        description=sanitize_csv_value(desc),
                        source_file=file_path.split("/")[-1],
                        line_number=line_num,
                    )
                    transactions.append(txn)

        return transactions

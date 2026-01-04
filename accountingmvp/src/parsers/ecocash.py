"""Ecocash export parser for messy string formats."""

import re

import pandas as pd

from src.models.transaction import RawTransaction

from .base import BaseParser
from .sanitizer import sanitize_csv_value


class EcocashParser(BaseParser):
    """
    Parser for Type B Ecocash Exports (Messy Strings).

    Handles various Ecocash export formats including:
    - Standard CSV exports
    - SMS-style transaction logs
    - PDF text extractions

    Common patterns:
    - "You have received $100.00 from John Doe (263771234567) on 15/01/2024"
    - "Transfer of $50.00 to Jane Smith completed. Ref: EC12345"
    """

    # Regex patterns for Ecocash transaction extraction
    PATTERNS = {
        "received": re.compile(
            r"(?:received|got)\s+\$?([\d,]+(?:\.\d{2})?)\s+"
            r"from\s+([A-Za-z\s]+)\s*"
            r"(?:\((\d+)\))?\s*"
            r"(?:on\s+)?(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})?",
            re.IGNORECASE,
        ),
        "sent": re.compile(
            r"(?:sent|transferred?|paid)\s+\$?([\d,]+(?:\.\d{2})?)\s+"
            r"to\s+([A-Za-z\s]+)\s*"
            r"(?:\((\d+)\))?\s*"
            r"(?:on\s+)?(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})?",
            re.IGNORECASE,
        ),
        "reference": re.compile(
            r"(?:ref(?:erence)?[:\s]*|txn[:\s]*|id[:\s]*)([A-Z0-9]+)", re.IGNORECASE
        ),
        "amount": re.compile(r"\$?([\d,]+(?:\.\d{2})?)"),
        "date": re.compile(r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})"),
    }

    # Expected CSV columns for structured Ecocash exports
    EXPECTED_COLS = {"date", "amount", "description"}
    ALTERNATE_COLS = {"transaction_date", "value", "details"}

    def validate(self, file_path: str) -> bool:
        """
        Validate if file is an Ecocash export.

        Checks for:
        - CSV with expected columns
        - Text file with Ecocash transaction patterns
        """
        try:
            # Try CSV validation first
            if file_path.endswith(".csv"):
                df = pd.read_csv(file_path, nrows=5)
                cols_lower = {c.lower() for c in df.columns}
                if self.EXPECTED_COLS.issubset(cols_lower):
                    return True
                if self.ALTERNATE_COLS.issubset(cols_lower):
                    return True

            # Try text-based validation
            with open(file_path, encoding="utf-8", errors="replace") as f:
                content = f.read(2000)  # Read first 2KB
                # Look for Ecocash patterns
                if any(
                    pattern in content.lower()
                    for pattern in ["ecocash", "econet", "received", "transferred"]
                ):
                    return True

            return False
        except Exception:
            return False

    def parse(self, file_path: str) -> list[RawTransaction]:
        """
        Parse Ecocash export file.

        Handles both structured CSV and unstructured text formats.
        """
        # Try structured CSV first
        if file_path.endswith(".csv"):
            try:
                return self._parse_csv(file_path)
            except Exception:
                pass

        # Fall back to text parsing
        return self._parse_text(file_path)

    def _parse_csv(self, file_path: str) -> list[RawTransaction]:
        """Parse structured Ecocash CSV export."""
        df = pd.read_csv(file_path)

        # Normalize column names
        df.columns = df.columns.str.lower().str.strip()

        # Map columns to standard names
        col_mapping = {
            "transaction_date": "date",
            "value": "amount",
            "details": "description",
            "trans_date": "date",
            "trans_amount": "amount",
        }
        df = df.rename(columns=col_mapping)

        transactions = []
        for idx, row in df.iterrows():
            # Extract fields with fallbacks
            date_val = str(row.get("date", ""))
            amount_val = str(row.get("amount", "0"))
            desc_val = str(row.get("description", ""))
            ref_val = str(row.get("reference", row.get("ref", "")))

            # Try to extract reference from description if not present
            if not ref_val:
                ref_match = self.PATTERNS["reference"].search(desc_val)
                if ref_match:
                    ref_val = ref_match.group(1)

            txn = RawTransaction(
                raw_date=date_val,
                raw_amount=amount_val.replace(",", ""),
                raw_reference=sanitize_csv_value(ref_val),
                description=sanitize_csv_value(desc_val),
                source_file=file_path.split("/")[-1],
                line_number=idx + 2,
            )
            transactions.append(txn)

        return transactions

    def _parse_text(self, file_path: str) -> list[RawTransaction]:
        """Parse unstructured Ecocash text export (SMS logs, etc.)."""
        transactions = []

        with open(file_path, encoding="utf-8", errors="replace") as f:
            lines = f.readlines()

        for line_num, line in enumerate(lines, start=1):
            line = line.strip()
            if not line:
                continue

            txn = self._extract_transaction_from_text(line, file_path, line_num)
            if txn:
                transactions.append(txn)

        return transactions

    def _extract_transaction_from_text(
        self, text: str, file_path: str, line_num: int
    ) -> RawTransaction | None:
        """Extract transaction details from a text line."""
        amount = None
        date = None
        description = text[:100]  # Use first 100 chars as description
        reference = ""

        # Try to match received pattern
        match = self.PATTERNS["received"].search(text)
        if match:
            amount = match.group(1)
            description = f"Received from {match.group(2).strip()}"
            date = match.group(4) if match.group(4) else ""

        # Try to match sent pattern
        if not amount:
            match = self.PATTERNS["sent"].search(text)
            if match:
                amount = f"-{match.group(1)}"  # Negative for outgoing
                description = f"Sent to {match.group(2).strip()}"
                date = match.group(4) if match.group(4) else ""

        # Extract reference
        ref_match = self.PATTERNS["reference"].search(text)
        if ref_match:
            reference = ref_match.group(1)

        # If no amount found, try generic extraction
        if not amount:
            amount_match = self.PATTERNS["amount"].search(text)
            if amount_match:
                amount = amount_match.group(1)

        # Try to find date if not found
        if not date:
            date_match = self.PATTERNS["date"].search(text)
            if date_match:
                date = date_match.group(1)

        # Only create transaction if we have amount
        if amount:
            return RawTransaction(
                raw_date=date or "",
                raw_amount=amount.replace(",", ""),
                raw_reference=sanitize_csv_value(reference),
                description=sanitize_csv_value(description),
                source_file=file_path.split("/")[-1],
                line_number=line_num,
            )

        return None

"""Data normalization pipeline."""

import hashlib
from datetime import date
from decimal import Decimal, InvalidOperation

from dateutil import parser as date_parser

from src.logger import setup_logger
from src.models.enums import TransactionSource
from src.models.transaction import NormalizedTransaction, RawTransaction

logger = setup_logger(__name__)


class NormalizationPipeline:
    """
    Pipeline for transforming raw transactions into normalized format.

    Stages:
    1. Parse date strings to date objects
    2. Parse amounts to Decimal
    3. Clean and standardize references
    4. Generate unique transaction IDs
    5. Deduplicate
    """

    def __init__(self, source: TransactionSource):
        self.source = source
        self._seen_hashes: set[str] = set()

    def process(
        self, raw_transactions: list[RawTransaction]
    ) -> list[NormalizedTransaction]:
        """
        Process list of raw transactions through normalization pipeline.

        Args:
            raw_transactions: List of raw parsed transactions

        Returns:
            List of normalized, deduplicated transactions
        """
        normalized = []

        for raw in raw_transactions:
            try:
                txn = self._normalize_single(raw)
                if txn and txn.id not in self._seen_hashes:
                    self._seen_hashes.add(txn.id)
                    normalized.append(txn)
            except Exception as e:
                logger.warning(
                    f"Failed to normalize transaction at line {raw.line_number}: {e}"
                )
                continue

        logger.info(
            f"Normalized {len(normalized)} transactions from {len(raw_transactions)} raw"
        )
        return normalized

    def _normalize_single(self, raw: RawTransaction) -> NormalizedTransaction | None:
        """Normalize a single transaction."""
        # Parse date
        txn_date = self._parse_date(raw.raw_date)
        if not txn_date:
            return None

        # Parse amount
        amount = self._parse_amount(raw.raw_amount)
        if amount is None:
            return None

        # Clean reference
        reference = self._clean_reference(raw.raw_reference)

        # Generate unique ID
        txn_id = self._generate_id(txn_date, amount, reference, raw.description)

        return NormalizedTransaction(
            id=txn_id,
            transaction_date=txn_date,
            amount=amount,
            reference=reference,
            description=raw.description.strip(),
            source=self.source.value,
            metadata={
                "source_file": raw.source_file,
                "line_number": raw.line_number,
            },
        )

    def _parse_date(self, date_str: str) -> date | None:
        """Parse various date formats into date object."""
        try:
            # dateutil handles most formats automatically
            parsed = date_parser.parse(date_str, dayfirst=True)
            return parsed.date()
        except (ValueError, TypeError):
            return None

    def _parse_amount(self, amount_str: str) -> Decimal | None:
        """Parse amount string to Decimal."""
        try:
            # Remove currency symbols and whitespace
            clean = amount_str.strip()
            clean = clean.replace("$", "").replace("£", "").replace("€", "")
            clean = clean.replace(" ", "").replace(",", "")

            # Handle parentheses for negative (accounting format)
            if clean.startswith("(") and clean.endswith(")"):
                clean = "-" + clean[1:-1]

            return Decimal(clean)
        except (InvalidOperation, ValueError):
            return None

    def _clean_reference(self, ref: str) -> str:
        """Standardize reference format."""
        return ref.strip().upper().replace(" ", "")

    def _generate_id(
        self, txn_date: date, amount: Decimal, reference: str, description: str
    ) -> str:
        """Generate unique hash ID for transaction."""
        content = f"{txn_date.isoformat()}|{amount}|{reference}|{description}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

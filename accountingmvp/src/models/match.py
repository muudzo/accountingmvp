"""Match result models for reconciliation."""
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field

from .enums import MatchConfidence, MatchStatus
from .transaction import NormalizedTransaction


class MatchScore(BaseModel):
    """Detailed breakdown of match scoring."""
    amount_score: float = Field(ge=0, le=1, description="Amount similarity (0-1)")
    text_score: float = Field(ge=0, le=1, description="Description/ref similarity (0-1)")
    date_score: float = Field(ge=0, le=1, description="Date proximity score (0-1)")
    reference_bonus: float = Field(ge=0, le=0.1, description="Exact reference match bonus")
    
    @property
    def total_score(self) -> float:
        """Calculate weighted total score."""
        return (
            0.4 * self.amount_score +
            0.3 * self.text_score +
            0.2 * self.date_score +
            self.reference_bonus
        )
    
    @property
    def confidence(self) -> MatchConfidence:
        """Determine confidence level from score."""
        score = self.total_score
        if score >= 0.90:
            return MatchConfidence.HIGH
        elif score >= 0.70:
            return MatchConfidence.MEDIUM
        elif score >= 0.50:
            return MatchConfidence.LOW
        return MatchConfidence.NONE


class MatchResult(BaseModel):
    """Represents a potential match between two transactions."""
    source_transaction: NormalizedTransaction
    target_transaction: NormalizedTransaction
    score: MatchScore
    status: MatchStatus = MatchStatus.UNMATCHED
    matched_by: str = "system"  # 'system' or 'manual'
    notes: Optional[str] = None
    
    @property
    def confidence_level(self) -> MatchConfidence:
        return self.score.confidence


class ReconciliationSummary(BaseModel):
    """Summary statistics for a reconciliation run."""
    total_source_transactions: int
    total_target_transactions: int
    matched_count: int
    unmatched_source_count: int
    unmatched_target_count: int
    manual_review_count: int
    match_rate: float = Field(ge=0, le=1)
    
    total_matched_amount: Decimal = Decimal("0")
    total_unmatched_amount: Decimal = Decimal("0")

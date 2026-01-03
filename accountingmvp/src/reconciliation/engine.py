"""Main reconciliation engine."""
from typing import List, Tuple, Optional
from decimal import Decimal

from src.models.transaction import NormalizedTransaction
from src.models.match import MatchResult, MatchScore, ReconciliationSummary
from src.models.enums import MatchStatus, MatchConfidence
from src.logger import setup_logger
from .scorer import ConfidenceScorer

logger = setup_logger(__name__)


class ReconciliationEngine:
    """
    Main orchestrator for transaction reconciliation.
    
    Multi-stage matching approach:
    1. Stage 1: Exact reference match (O(n))
    2. Stage 2: Amount + Date window filter (O(n log n))
    3. Stage 3: Fuzzy text matching on candidates (O(n²) worst case)
    4. Stage 4: Manual review queue for low confidence
    """
    
    def __init__(
        self, 
        confidence_threshold: float = 0.85,
        manual_review_threshold: float = 0.50
    ):
        """
        Initialize engine.
        
        Args:
            confidence_threshold: Minimum score for auto-match
            manual_review_threshold: Minimum score to consider for manual review
        """
        self.confidence_threshold = confidence_threshold
        self.manual_review_threshold = manual_review_threshold
        self.scorer = ConfidenceScorer()
    
    def reconcile(
        self, 
        source_transactions: List[NormalizedTransaction],
        target_transactions: List[NormalizedTransaction]
    ) -> Tuple[List[MatchResult], ReconciliationSummary]:
        """
        Run full reconciliation between source and target transactions.
        
        Args:
            source_transactions: e.g., bank statements
            target_transactions: e.g., invoices or payment records
            
        Returns:
            Tuple of (match_results, summary)
        """
        logger.info(
            f"Starting reconciliation: {len(source_transactions)} source, "
            f"{len(target_transactions)} target transactions"
        )
        
        matches: List[MatchResult] = []
        matched_source_ids: set = set()
        matched_target_ids: set = set()
        manual_review_count = 0
        
        # Build lookup index for targets
        target_index = {t.id: t for t in target_transactions}
        
        # Stage 1: Exact reference matching
        exact_matches, matched_source_ids, matched_target_ids = self._stage1_exact_match(
            source_transactions, target_transactions
        )
        matches.extend(exact_matches)
        
        # Stage 2 & 3: Fuzzy matching for remaining
        remaining_sources = [s for s in source_transactions if s.id not in matched_source_ids]
        remaining_targets = [t for t in target_transactions if t.id not in matched_target_ids]
        
        fuzzy_matches = self._stage23_fuzzy_match(remaining_sources, remaining_targets)
        
        for match in fuzzy_matches:
            if match.score.total_score >= self.confidence_threshold:
                match.status = MatchStatus.MATCHED
                matched_source_ids.add(match.source_transaction.id)
                matched_target_ids.add(match.target_transaction.id)
            elif match.score.total_score >= self.manual_review_threshold:
                match.status = MatchStatus.MANUAL_REVIEW
                manual_review_count += 1
            matches.append(match)
        
        # Calculate summary
        summary = self._build_summary(
            source_transactions,
            target_transactions,
            matched_source_ids,
            matched_target_ids,
            manual_review_count
        )
        
        logger.info(f"Reconciliation complete: {summary.matched_count} matches found")
        return matches, summary
    
    def _stage1_exact_match(
        self,
        sources: List[NormalizedTransaction],
        targets: List[NormalizedTransaction]
    ) -> Tuple[List[MatchResult], set, set]:
        """Exact reference matching - O(n)."""
        matches = []
        matched_source_ids = set()
        matched_target_ids = set()
        
        # Build reference index
        target_by_ref = {}
        for t in targets:
            if t.reference:
                target_by_ref[t.reference.upper()] = t
        
        for source in sources:
            if not source.reference:
                continue
            
            ref = source.reference.upper()
            if ref in target_by_ref:
                target = target_by_ref[ref]
                
                # Verify amount matches too
                score = self.scorer.calculate_score(source, target)
                if score.amount_score >= 0.95:
                    match = MatchResult(
                        source_transaction=source,
                        target_transaction=target,
                        score=score,
                        status=MatchStatus.MATCHED,
                        matched_by="exact_reference"
                    )
                    matches.append(match)
                    matched_source_ids.add(source.id)
                    matched_target_ids.add(target.id)
        
        logger.info(f"Stage 1 (exact): {len(matches)} matches")
        return matches, matched_source_ids, matched_target_ids
    
    def _stage23_fuzzy_match(
        self,
        sources: List[NormalizedTransaction],
        targets: List[NormalizedTransaction]
    ) -> List[MatchResult]:
        """Fuzzy matching for remaining transactions."""
        matches = []
        used_targets = set()
        
        for source in sources:
            best_match: Optional[MatchResult] = None
            best_score = 0.0
            
            for target in targets:
                if target.id in used_targets:
                    continue
                
                score = self.scorer.calculate_score(source, target)
                total = score.total_score
                
                if total > best_score and total >= self.manual_review_threshold:
                    best_score = total
                    best_match = MatchResult(
                        source_transaction=source,
                        target_transaction=target,
                        score=score,
                        status=MatchStatus.UNMATCHED,
                        matched_by="fuzzy"
                    )
            
            if best_match:
                matches.append(best_match)
                if best_match.score.total_score >= self.confidence_threshold:
                    used_targets.add(best_match.target_transaction.id)
        
        logger.info(f"Stage 2/3 (fuzzy): {len(matches)} potential matches")
        return matches
    
    def _build_summary(
        self,
        sources: List[NormalizedTransaction],
        targets: List[NormalizedTransaction],
        matched_source_ids: set,
        matched_target_ids: set,
        manual_review_count: int
    ) -> ReconciliationSummary:
        """Build reconciliation summary statistics."""
        matched_amount = sum(
            s.amount for s in sources if s.id in matched_source_ids
        )
        unmatched_amount = sum(
            s.amount for s in sources if s.id not in matched_source_ids
        )
        
        return ReconciliationSummary(
            total_source_transactions=len(sources),
            total_target_transactions=len(targets),
            matched_count=len(matched_source_ids),
            unmatched_source_count=len(sources) - len(matched_source_ids),
            unmatched_target_count=len(targets) - len(matched_target_ids),
            manual_review_count=manual_review_count,
            match_rate=len(matched_source_ids) / len(sources) if sources else 0.0,
            total_matched_amount=matched_amount,
            total_unmatched_amount=unmatched_amount
        )

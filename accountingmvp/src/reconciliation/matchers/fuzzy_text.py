"""Fuzzy text matching using RapidFuzz."""
from rapidfuzz import fuzz
from rapidfuzz.distance import Levenshtein

from src.models.transaction import NormalizedTransaction


class FuzzyTextMatcher:
    """
    Fuzzy string matching for transaction descriptions and references.
    
    Uses multiple algorithms and returns the best score:
    - Ratio: Simple character-level similarity
    - Partial Ratio: Best substring match
    - Token Sort: Order-independent word matching
    - Token Set: Handles duplicates and order
    """
    
    def __init__(self, threshold: float = 0.70):
        """
        Initialize matcher.
        
        Args:
            threshold: Minimum score (0-1) to consider a match
        """
        self.threshold = threshold
    
    def score(self, txn1: NormalizedTransaction, txn2: NormalizedTransaction) -> float:
        """
        Calculate text similarity between two transactions.
        
        Compares both description and reference fields.
        
        Returns:
            Similarity score from 0 to 1
        """
        # Compare descriptions
        desc_score = self._best_match(txn1.description, txn2.description)
        
        # Compare references
        ref_score = self._best_match(txn1.reference, txn2.reference)
        
        # Weight descriptions more heavily, but give bonus for reference match
        if ref_score > 0.95:  # Near-exact reference match
            return min(1.0, 0.6 * desc_score + 0.4 * ref_score + 0.1)
        
        return 0.7 * desc_score + 0.3 * ref_score
    
    def _best_match(self, str1: str, str2: str) -> float:
        """Get best match score using multiple algorithms."""
        if not str1 or not str2:
            return 0.0
        
        # Normalize strings
        s1 = str1.lower().strip()
        s2 = str2.lower().strip()
        
        # Try multiple algorithms and take the best
        scores = [
            fuzz.ratio(s1, s2) / 100,
            fuzz.partial_ratio(s1, s2) / 100,
            fuzz.token_sort_ratio(s1, s2) / 100,
            fuzz.token_set_ratio(s1, s2) / 100,
        ]
        
        return max(scores)
    
    def is_match(self, txn1: NormalizedTransaction, txn2: NormalizedTransaction) -> bool:
        """Check if two transactions match based on threshold."""
        return self.score(txn1, txn2) >= self.threshold

# Architecture Decision Record: Matching Algorithm Design

## Status
Accepted

## Context
The core value proposition is matching payments from bank statements against invoices/payment records. Matching must handle:
- Exact matches (same reference, amount)
- Near matches (slightly different descriptions)
- Fuzzy matches (similar but not identical)
- Time proximity (transactions on nearby dates)

## Decision
Implement a **multi-stage matching pipeline** with configurable confidence thresholds.

### Stages

```
Stage 1: Exact Reference Match (O(n))
    ↓
Stage 2: Amount + Date Window Filter (O(n log n))
    ↓
Stage 3: Fuzzy Text Matching (O(n²) worst case)
    ↓
Stage 4: Manual Review Queue
```

### Confidence Scoring

```python
confidence = (
    0.40 * amount_match_score +
    0.30 * text_similarity_score +
    0.20 * date_proximity_score +
    0.10 * reference_match_bonus
)
```

### Thresholds
- **Auto-Match**: confidence ≥ 85%
- **Manual Review**: 50% ≤ confidence < 85%
- **No Match**: confidence < 50%

## Consequences

### Positive
- **Performance**: Early stages filter quickly, expensive fuzzy matching only on candidates
- **Accuracy**: Multiple signals reduce false positives
- **Human-in-loop**: Low confidence matches go to manual review
- **Tunable**: Weights and thresholds can be adjusted

### Negative
- O(n²) worst case for fuzzy matching
- Requires tuning for optimal accuracy

## Algorithms

### Text Similarity
Using RapidFuzz library with multiple algorithms:
- `fuzz.ratio`: Simple character similarity
- `fuzz.partial_ratio`: Best substring match
- `fuzz.token_sort_ratio`: Order-independent word matching
- `fuzz.token_set_ratio`: Handles duplicates

Best score from all algorithms is used.

### Amount Matching
- **Percentage tolerance**: ±2% (configurable)
- **Absolute tolerance**: $0.01 for small amounts
- Handles currency symbol variations

### Date Matching
- **Window**: ±3 days (configurable)
- Linear score decay within window
- 0 score outside window

## Alternatives Considered

1. **Single-pass exact matching**
   - Rejected: Too restrictive, misses valid matches
   
2. **Machine Learning classifier**
   - Rejected: Requires training data; can add later as enhancement
   
3. **External matching service**
   - Rejected: Adds dependency, latency, and cost

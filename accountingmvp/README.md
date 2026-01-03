# Payment Reconciliation MVP

> **"Excel Killer"** - A production-grade payment reconciliation system with fuzzy matching for heterogeneous financial data.

![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![Streamlit](https://img.shields.io/badge/streamlit-1.28+-red.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## Overview

This system ingests financial data from multiple sources (bank statements, Ecocash, ZIPIT), normalizes them into a unified ledger, and performs intelligent fuzzy matching to reconcile payments against invoices.

### Features

✅ **Multi-Source Ingestion**: Parse CSV bank statements, Ecocash exports, ZIPIT text files  
✅ **Security First**: CSV injection prevention, input sanitization, Zero Trust approach  
✅ **Fuzzy Matching**: Multi-algorithm text matching (Levenshtein, Jaro-Winkler, Token Sort)  
✅ **Confidence Scoring**: Weighted scoring system combining amount, text, and date signals  
✅ **Interactive Dashboard**: Streamlit-based UI for file upload, review, and export  
✅ **Report Generation**: Export reconciliation results to CSV/Excel  

## Quick Start

### Prerequisites

- Python 3.11+
- pip or pipenv

### Installation

```bash
# Clone the repository
cd accountingmvp

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Running the Application

```bash
# Start the Streamlit dashboard
streamlit run dashboard/app.py
```

The app will open at `http://localhost:8501`.

## Project Structure

```
accountingmvp/
├── src/                    # Core business logic
│   ├── models/             # Pydantic data models
│   ├── parsers/            # CSV/TXT parsers + sanitization
│   ├── normalizer/         # Data transformation pipeline
│   └── reconciliation/     # Matching engine + scoring
├── dashboard/              # Streamlit application
├── tests/                  # Unit + integration tests
├── data/                   # Runtime data (gitignored)
└── docs/                   # Documentation
```

## Usage

1. **Upload Files**: Use the sidebar to upload your bank statement (CSV) and payment records (CSV/TXT)
2. **Configure Settings**: Adjust confidence threshold for auto-matching
3. **Run Reconciliation**: Click the button to start the matching process
4. **Review Results**: View matched, unmatched, and manual review items
5. **Download Report**: Export results to CSV

## File Formats

### Bank Statement (Type A)
```csv
Date,Reference,Amount,Description
2024-01-15,TXN001,1500.00,Payment from ABC Corp
```

### Ecocash Export (Type B)
```csv
Date,Reference,Amount,Description
15/01/2024,EC001,1500,ABC Corporation payment
```

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_parsers.py -v
```

### Code Quality

```bash
# Format code
black src/ dashboard/ tests/

# Lint
ruff check src/ dashboard/

# Type check
mypy src/
```

## Architecture

### Matching Algorithm

The reconciliation engine uses a multi-stage approach:

1. **Stage 1: Exact Match** - O(n) hash lookup on transaction references
2. **Stage 2: Amount + Date Filter** - Narrows candidates by amount (±2%) and date (±3 days)
3. **Stage 3: Fuzzy Text Matching** - RapidFuzz similarity on descriptions
4. **Stage 4: Manual Review** - Low-confidence matches queued for human review

### Confidence Scoring

```
confidence = (
    0.4 * amount_match_score +
    0.3 * text_similarity_score +
    0.2 * date_proximity_score +
    0.1 * reference_match_bonus
)
```

## Security

- **CSV Injection Prevention**: Formula characters (=, +, -, @) are neutralized
- **Input Validation**: File size limits, format verification
- **No PII in Logs**: Sensitive data is redacted

## License

MIT License - See LICENSE for details.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

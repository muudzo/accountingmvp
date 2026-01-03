# Architecture Decision Record: Parser Strategy Pattern

## Status
Accepted

## Context
We need to parse heterogeneous financial data from multiple sources:
- Bank CSV statements (Type A)
- Ecocash exports (Type B)
- ZIPIT text files

Each format has different column structures, date formats, and data patterns.

## Decision
Implement the **Strategy Pattern** with an abstract base class and a factory for parser selection.

### Structure
```
BaseParser (ABC)
├── BankCSVParser
├── EcocashParser
└── ZIPITParser

ParserFactory
└── get_parser(file_path) -> BaseParser
```

### Interface
```python
class BaseParser(ABC):
    @abstractmethod
    def parse(self, file_path: str) -> List[RawTransaction]: ...
    
    @abstractmethod
    def validate(self, file_path: str) -> bool: ...
```

## Consequences

### Positive
- **Extensibility**: Adding new data sources requires only implementing the `BaseParser` interface
- **Testability**: Each parser can be unit tested independently
- **Separation of Concerns**: Each parser handles exactly one format
- **Open/Closed Principle**: System is open for extension, closed for modification

### Negative
- Slight overhead from polymorphism
- Factory logic can become complex with many parsers

## Alternatives Considered

1. **Single parser with format detection**
   - Rejected: Would violate Single Responsibility Principle
   
2. **Configuration-based parsing**
   - Rejected: Too inflexible for complex format variations
   
3. **Plugin architecture with dynamic loading**
   - Rejected: Overkill for MVP; can migrate later if needed

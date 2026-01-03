"""Parser factory for automatic format detection."""
from typing import Optional, Type
from .base import BaseParser
from .bank_csv import BankCSVParser
from .ecocash import EcocashParser
from .zipit import ZIPITParser


class ParserFactory:
    """
    Factory for creating appropriate parser based on file format.
    
    Uses file extension and content sniffing to detect format.
    """
    
    # Registry of parsers in priority order
    PARSERS: list[Type[BaseParser]] = [
        BankCSVParser,
        EcocashParser,
        ZIPITParser,
    ]
    
    @classmethod
    def get_parser(cls, file_path: str) -> Optional[BaseParser]:
        """
        Detect file format and return appropriate parser.
        
        Args:
            file_path: Path to the file to parse
            
        Returns:
            Parser instance or None if format not recognized
        """
        # Try each parser's validation
        for parser_class in cls.PARSERS:
            parser = parser_class()
            try:
                if parser.validate(file_path):
                    return parser
            except Exception:
                continue
        
        return None
    
    @classmethod
    def get_parser_by_type(cls, parser_type: str) -> Optional[BaseParser]:
        """
        Get parser by explicit type name.
        
        Args:
            parser_type: One of 'bank', 'ecocash', 'zipit'
            
        Returns:
            Parser instance
        """
        type_map = {
            'bank': BankCSVParser,
            'ecocash': EcocashParser,
            'zipit': ZIPITParser,
        }
        
        parser_class = type_map.get(parser_type.lower())
        if parser_class:
            return parser_class()
        return None

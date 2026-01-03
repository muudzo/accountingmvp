from abc import ABC, abstractmethod
from typing import List
from src.models.transaction import RawTransaction

class BaseParser(ABC):
    @abstractmethod
    def parse(self, file_path: str) -> List[RawTransaction]:
        """Parse file and return list of raw transactions."""
        pass
    
    @abstractmethod
    def validate(self, file_path: str) -> bool:
        """Validate file format/headers before parsing."""
        pass

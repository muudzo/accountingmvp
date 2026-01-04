from abc import ABC, abstractmethod

from src.models.transaction import RawTransaction


class BaseParser(ABC):
    @abstractmethod
    def parse(self, file_path: str) -> list[RawTransaction]:
        """Parse file and return list of raw transactions."""
        pass

    @abstractmethod
    def validate(self, file_path: str) -> bool:
        """Validate file format/headers before parsing."""
        pass

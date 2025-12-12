from abc import ABC, abstractmethod

class StorageProvider(ABC):
    @abstractmethod
    def save_report(self, report_data: dict) -> bool:
        """Save LLM analysis report to persistent storage."""
        pass
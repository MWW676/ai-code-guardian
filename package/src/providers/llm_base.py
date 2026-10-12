from abc import ABC, abstractmethod

class LLMProvider(ABC):
    @abstractmethod
    def analyze_diff(self, contents: str) -> dict:
        """Analyze a code diff with prompt by an AI client."""
        pass
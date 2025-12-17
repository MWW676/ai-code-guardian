from abc import ABC, abstractmethod

class GithubProvider(ABC):
    @abstractmethod
    def get_diff(self, repo_full_name: str, pr_number: int) -> str:
        """Return diff plaintext from Github Pull request."""
        pass
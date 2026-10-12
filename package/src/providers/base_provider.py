from abc import ABC, abstractmethod

class GitProvider(ABC):
    @abstractmethod
    def get_diff(self, repo_full_name: str, pr_number: int) -> str:
        pass

    @abstractmethod
    def post_comment(self,repo_full_name: str, pr_number: int, pr_comments: str) -> bool:
        pass

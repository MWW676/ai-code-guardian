from enum import Enum

class GitPlatform(str, Enum):
    GITHUB = 'github'
    GITLAB = 'gitlab'
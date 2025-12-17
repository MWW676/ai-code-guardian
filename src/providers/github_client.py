import os
import logging
import requests
from src.providers.github_base import GithubProvider

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class GithubClient(GithubProvider):
    def __init__(self):
        self.api_key = os.environ.get('GITHUB_API_KEY')
        if not self.api_key:
            raise EnvironmentError("GITHUB_API_KEY not found in env variables.")
        self.base_url = "https://api.github.com"

    def get_diff(self, repo_full_name: str, pr_number: int) -> str:
        # Construct complete path for GET diff request
        diff_path = f'{self.base_url}/repos/{repo_full_name}/pulls/{str(pr_number)}'
        headers = {
            "Accept": "application/vnd.github.v3.diff",
            "Authorization": f"Bearer {self.api_key}"
        }

        try:
            response = requests.get(url=diff_path, headers=headers, timeout=10)
            if response.status_code == 200:
                logger.info(f"Successfully fetch diff for PR#{pr_number} ({len(response.text)} chars)")
                return response.text
            else:
                logger.warning(f"Github API error: {response.status_code} - {response.text[:100]}")
                return 'ERROR'

        except requests.exceptions.RequestException as e:
            logger.error(f"Network error while fetching diff: {str(e)}")
            return 'ERROR'

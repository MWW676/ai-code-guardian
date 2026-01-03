
import logging
import requests
from src.providers.base_provider import GitProvider

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class GitlabClient(GitProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key
        if not self.api_key:
            raise EnvironmentError("GITLAB_API_KEY not found in SSM configs.")
        self.base_url = "https://gitlab.com/api/v4"

    def get_diff(self, repo_full_name: str, pr_number: int) -> str:
        """
        :param repo_full_name: maps to project_id
        :param pr_number: maps to ::iid
        """
        diff_path = f'{self.base_url}/projects/{repo_full_name}/merge_requests/{str(pr_number)}/diffs'
        headers = {
            "Accept": "application/json",
            "Private-Token": f"{self.api_key}"
        }

        try:
            response = requests.get(url=diff_path, headers=headers, timeout=10)
            if response.status_code == 200:
                logger.info(f"Successfully fetch diff for PR #{pr_number} ({len(response.text)} chars)")
                diffs = response.json()
                combined_diff = "\n".join([item.get('diff', '') for item in diffs])
                return combined_diff
            else:
                logger.warning(f"Gitlab API error: {response.status_code} - {response.text[:100]}")
                return 'ERROR'

        except requests.exceptions.RequestException as e:
            logger.error(f"Network error while fetching diff: {str(e)}")
            return 'ERROR'

    def post_comment(self, repo_full_name: str, pr_number: int, pr_comments: str) -> bool:
        """
        :param repo_full_name: maps to project_id
        :param pr_number: maps to ::iid
        """
        post_comment_path = f'{self.base_url}/projects/{repo_full_name}/merge_requests/{str(pr_number)}/notes'
        headers = {
            "Accept": "application/json",
            "Private-Token": f"{self.api_key}"
        }
        payload = {"body": pr_comments}

        try:
            response = requests.post(url=post_comment_path, headers=headers, json=payload, timeout=10)
            if response.status_code == 201:
                logger.info(f"Successfully posted comment for PR #{pr_number} ({len(response.text)} chars)")
                return True
            else:
                logger.warning(f"Gitlab API error: {response.status_code} - {response.text}")
                return False

        except requests.exceptions.RequestException as e:
            logger.error(f"Network error while posting comment: {str(e)}")
            return False

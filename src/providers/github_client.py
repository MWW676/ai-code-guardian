import os
import logging
import requests
from dotenv import load_dotenv
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
            response = requests.get(url=diff_path, headers=headers)
            if response.status_code == 200:
                logger.info(f"Get Git diff successful: {response.text}")
                return response.text
            else:
                logger.warning(f"Get Git diff failed: {response.json()}")
                return 'ERROR'
        except RuntimeError as e:
            logger.error(f"Runtime error from Github API GET req: {str(e)}")
            return 'ERROR'
        except Exception as e:
            logger.error(f"Unexpected error from Github API GET req: {str(e)}")
            return 'ERROR'

if __name__ == "__main__":
    load_dotenv()
    github_client = GithubClient()
    res = github_client.get_diff(repo_full_name='fang407/learning', pr_number=1)
    print(res)
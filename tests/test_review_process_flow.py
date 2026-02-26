from src.providers.github_client import GithubClient
from src.providers.gemini_client import GeminiClient
import logging

logger = logging.getLogger(__name__)

def test_review_process_flow(mock_requests_lib, mock_gemini_client):
    repo_name, pr_number = "dummy_repo", 1

    logger.info("Calling mock github to retrieve code diff.")
    git_client = GithubClient(api_key="fake")
    diff = git_client.get_diff(repo_full_name=repo_name, pr_number=pr_number)
    assert 'hello world' in diff
    mock_requests_lib.get.assert_called_once()

    logger.info("Calling mock gemini to perform diff analysis.")
    gemini_client = GeminiClient(api_key="fake")
    resp = gemini_client.analyze_diff(contents=diff)
    assert resp["status"] == "PASS"
    mock_gemini_client.models.generate_content.assert_called_once()

    logger.info(f"Posting code review report for repo: {repo_name}, PR#{pr_number}.")
    comment_success = git_client.post_comment(repo_full_name=repo_name, pr_number=pr_number, pr_comments=resp)
    assert comment_success is True

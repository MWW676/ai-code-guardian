from src.providers.github_client import GithubClient
from requests.exceptions import RequestException

def test_github_client_functions(mock_requests_lib):
    client = GithubClient(api_key="fake")
    diff = client.get_diff(repo_full_name="fake", pr_number=1)
    assert "hello world" in diff
    mock_requests_lib.get.assert_called_once()

    comment_success = client.post_comment(repo_full_name="fake", pr_number=1, pr_comments="Nice code!")
    assert comment_success is True
    mock_requests_lib.post.assert_called_once()

    args, kwargs = mock_requests_lib.post.call_args
    assert kwargs['json']['body'] == "Nice code!"

def test_get_diff_failure(mock_requests_lib, mock_github_responses):
    mock_requests_lib.get.return_value = mock_github_responses(
        status_code=404,
        text="Diff not found"
    )
    client = GithubClient(api_key="fake")
    diff = client.get_diff(repo_full_name="fake", pr_number=1)
    assert diff == 'ERROR'

def test_post_comment_failure(mock_requests_lib, mock_github_responses):
    mock_requests_lib.post.return_value = mock_github_responses(
        status_code=500,
        text="Internal server error"
    )
    client = GithubClient(api_key="fake")
    comment_success = client.post_comment(repo_full_name="fake", pr_number=1, pr_comments="Nice code!")
    assert comment_success is False

def test_github_exception(mock_requests_lib):
    mock_requests_lib.get.side_effect = RequestException("Network error.")
    client = GithubClient(api_key="fake")
    diff = client.get_diff(repo_full_name="fake", pr_number=1)
    assert diff == 'ERROR'

    mock_requests_lib.post.side_effect = RequestException("Network error.")
    comment_success = client.post_comment(repo_full_name="fake", pr_number=1, pr_comments="Nice code!")
    assert comment_success is False
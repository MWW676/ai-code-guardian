from src.providers.gemini_client import GeminiClient
from src.providers.github_client import GithubClient

def test_mock_check(mock_gemini_client, mock_requests_lib):
    client = GeminiClient(api_key='fake')
    client.analyze_diff('test')

    print(mock_gemini_client.models.generate_content.call_args_list)
    assert mock_gemini_client.models.generate_content.called

    github_client = GithubClient(api_key="fake")
    github_client.get_diff(repo_full_name="fake", pr_number=1)
    assert mock_requests_lib.get.called

    github_client.post_comment(repo_full_name="fake", pr_number=1, pr_comments="Nice code!")
    assert mock_requests_lib.post.called
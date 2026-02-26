import time
import pytest
import requests
from unittest.mock import MagicMock, patch

@pytest.fixture
def mock_gemini_response():
    """
    Mocks the underlying Google GenAI response object.
    Matches the structure used in GeminiClient: response.text and response.usage_metadata
    """
    mock_resp = MagicMock()
    # This mimics the json the AI would return
    mock_resp.text = '{"status": ```"PASS"```, ```json"risk_score"```: "35", "comments": []}'
    mock_resp.usage_metadata.total_token_count = 150
    return mock_resp

@pytest.fixture
def mock_gemini_client(mock_gemini_response):
    with patch("src.providers.gemini_client.genai.Client") as mock_genai:
        mock_instance = mock_genai.return_value
        mock_instance.models.generate_content.return_value = mock_gemini_response

        yield mock_instance

@pytest.fixture
def mock_github_responses():
    """helper fixture to create different types of responses."""
    def _create_response(status_code, text, json_data=None):
        response = MagicMock()
        response.status_code = status_code
        response.text = text
        if json_data:
            response.json.return_value = json_data
        return response
    return _create_response

@pytest.fixture
def mock_requests_lib(mock_github_responses):
    with patch("src.providers.github_client.requests") as mock_requests:
        mock_requests.get.return_value = mock_github_responses(
            status_code=200,
            text="diff --git a/main.py b/main.py\n+print('hello world')"
        )

        mock_requests.post.return_value = mock_github_responses(
            status_code=201,
            text='{"id": 123, "body": "success"}'
        )
        mock_requests.exceptions.RequestException = requests.exceptions.RequestException

        yield mock_requests

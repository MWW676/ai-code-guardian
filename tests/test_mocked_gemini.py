
from google.genai.errors import APIError
from src.providers.gemini_client import GeminiClient

def test_gemini_rpd_limit_exceeded(mock_gemini_client):
    client = GeminiClient(api_key="fake")
    client.DAILY_REQUEST_COUNT = 20

    result = client.analyze_diff("some fake code diff")
    assert result["status"] == "SKIPPED"
    assert "Rate/Token limit exceeded." in result["reason"]

    mock_gemini_client.models.generate_content.assert_not_called()

def test_gemini_successful_parsing(mock_gemini_client):
    client = GeminiClient(api_key='fake')
    resp = client.analyze_diff('dummy diff')

    assert isinstance(resp, dict)
    assert resp['result']['status'] == 'PASS'
    assert resp['token_used'] == 150

def test_gemini_failed_parsing(mock_gemini_client, mock_gemini_response):
    mock_gemini_response.text = '{"status": "PASS", "risk_score": '

    client = GeminiClient(api_key="fake")
    resp = client.analyze_diff("dummy diff")
    assert resp["status"] == "ERROR"

def test_gemini_API_error(mock_gemini_client):
    mock_gemini_client.models.generate_content.side_effect = APIError(
        code=500,
        response_json={"Message": "Internal Server Error."}
    )

    client = GeminiClient(api_key="fake")
    result = client.analyze_diff("dummy diff")
    assert result["status"] == "ERROR"
    assert "Internal Server Error." in result["error"]

def test_gemini_unexpected_exception(mock_gemini_client):
    mock_gemini_client.models.generate_content.side_effect = Exception("System crash.")

    client = GeminiClient(api_key="fake")
    result = client.analyze_diff("dummy diff")
    assert result["status"] == "ERROR"
    assert "System crash" in result["error"]
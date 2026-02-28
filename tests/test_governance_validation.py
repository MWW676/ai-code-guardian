import pytest
from tests import logger
from src.providers.gemini_client import GeminiClient
from src.core.models import ReportModel
from pydantic import ValidationError

def test_policy_misalignment_detection(mock_gemini_client, mock_gemini_response):
    requested_policy = "EFFICIENCY_FIRST"
    client = GeminiClient(api_key="fake", policy_name=requested_policy)

    mock_gemini_response.text = '''{
        "status": "PASS", 
        "risk_score": 5, 
        "applied_policy": "SECURITY_FIRST",
        "policy_alignment_score": 90,
        "comments": []
    }'''
    resp = client.analyze_diff("dummy diff")
    actual_policy = resp["result"].get("applied_policy")
    logger.info(f"Requested: {requested_policy} | AI claimed: {actual_policy}")

    if actual_policy != requested_policy:
        logger.warning("Governance breach detected: AI used wrong policy lens!")
        assert actual_policy != requested_policy

    model = ReportModel(**resp["result"])
    assert model.applied_policy == "SECURITY_FIRST"

def test_low_alignment_score_rejection():
    bad_data = {
        "status": "PASS",
        "risk_score": 10,
        "applied_policy": "SECURITY_FIRST",
        "policy_alignment_score": 30,
        "comments": []
    }

    with pytest.raises(ValidationError) as exc_info:
        ReportModel(**bad_data)

    assert "AI alignment score is too low" in str(exc_info.value)
    logger.info("Successfully rejected AI review with low alignment score.")
import pytest
import logging
from src.providers.gemini_client import GeminiClient

logger = logging.getLogger(__name__)

@pytest.mark.parametrize("policy_name, expected_keyword", [
    ("SECURITY_FIRST", "Security Architect"),
    ("EFFICIENCY_FIRST", "Performance Engineer"),
    ("COMPLIANCE_STRICT", "Lead Developer")
])
def test_policy_injection_logic(mock_gemini_client, policy_name, expected_keyword):
    client = GeminiClient(api_key="fake", policy_name=policy_name)
    client.analyze_diff("dummy diff")

    args, kwargs = mock_gemini_client.models.generate_content.call_args
    sent_system_instruction = kwargs['config'].system_instruction

    assert f"ACTIVE POLICY: {policy_name}" in sent_system_instruction
    assert expected_keyword in sent_system_instruction
    logger.info(f"\n✅ Verified: Policy '{policy_name}' injected '{expected_keyword}' into AI prompt.")

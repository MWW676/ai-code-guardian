
import json
import time
import yaml
import logging
from google import genai
from google.genai import types
from google.genai.errors import APIError
from src.providers.llm_base import LLMProvider
from src.core.models import ReportModel
from src.utils.prompt_utils import render_system_instrcution_prompt, render_user_message_prompt
from pathlib import Path

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

class GeminiClient(LLMProvider):
    def __init__(self, api_key: str, policy_name: str = 'SECURITY_FIRST'):
        if not api_key:
            raise EnvironmentError("GEMINI_API_KEY not found SSM configs.")
        self.client = genai.Client(api_key=api_key)
        self.model_name = "gemini-2.5-flash"
        self.policy_name = policy_name
        self.policies = self._load_policies()

        # --- Define Known Limits ---
        self._MAX_RPD: int = 20
        self._MAX_TPM: int = 250_000
        self._max_output_tokens = 6000
        # --- Global Tracking Variables ---
        self.DAILY_REQUEST_COUNT: int = 0
        self.LAST_REQUEST_TIME: float = time.time()
        self.CURRENT_MINUTE_TOKEN_COUNT: int = 0

    def _load_policies(self):
        policy_path = Path(__file__).parent.parent / "core" / "policies.yaml"
        with open(policy_path, "r") as f:
            return yaml.safe_load(f)

    def check_and_reset_limits(self, contents: str):
        """
        1. Checks the time and resets the RPD or TPM counters if necessary.
        2. Checks token count to ensure its below threshold.
        """
        now = time.time()
        elapsed_minutes = (now - self.LAST_REQUEST_TIME) / 60
        elapsed_days = (now - self.LAST_REQUEST_TIME) / (60 * 60 * 24)

        # 1. Reset TPM/RPM counter if a minute has passed
        if elapsed_minutes >= 1:
            logger.info(f"Resetting TPM count (last minute total: {self.CURRENT_MINUTE_TOKEN_COUNT} tokens).")
            self.CURRENT_MINUTE_TOKEN_COUNT = 0
            self.LAST_REQUEST_TIME = now

        # 2. Reset RPD counter if a day has passed
        if elapsed_days >= 1:
            logger.info(f"Resetting RPD count (last day total: {self.DAILY_REQUEST_COUNT} requests).")
            self.DAILY_REQUEST_COUNT = 0

        # 3. RPD Check (Most critical for free tier)
        if self.DAILY_REQUEST_COUNT >= self._MAX_RPD:
            logger.warning(f"[LIMIT EXCEEDED] RPD limit of {self._MAX_RPD} reached. Skipping API call.")
            return False

        # 4. TPM Check (Pre-calculate input cost)
        input_tokens = len(contents) / 4
        potential_total_tokens = input_tokens + self._max_output_tokens

        if self.CURRENT_MINUTE_TOKEN_COUNT + potential_total_tokens > self._MAX_TPM:
            logger.warning(f"TPM limit would be exceeded. Skipping API call.")
            return False

        # 5. Always update the last request time
        self.LAST_REQUEST_TIME = now
        return True

    def generate_system_instruction(self) -> str:
        # Construct prompt
        policy_content = self.policies.get(self.policy_name, self.policies["SECURITY_FIRST"])
        persona_instruction = policy_content["instruction"]

        schema_dict = ReportModel.model_json_schema()
        schema_str = json.dumps(schema_dict, indent=2)

        sys_instruction = render_system_instrcution_prompt(
            policy_name=self.policy_name,
            persona_instruction=persona_instruction,
            schema_str=schema_str
        )
        return sys_instruction

    def analyze_diff(self, contents: str) -> dict:
        """Generates content through Gemini open api call."""
        sys_instruction = self.generate_system_instruction()
        user_message = render_user_message_prompt(diff_content=contents)

        if not self.check_and_reset_limits(contents=user_message):
            logger.warning("Limit or token quota check failed.")
            return {"status":"SKIPPED", "reason": "Rate/Token limit exceeded."}

        try:
            logger.info(f"Evaluating code diff with model: {self.model_name}...")
            config_object = types.GenerateContentConfig(
                max_output_tokens=self._max_output_tokens,
                response_mime_type="application/json",
                system_instruction=sys_instruction,
                temperature=0.1
            )

            response = self.client.models.generate_content(
                model=self.model_name,
                contents=user_message,
                config=config_object,
            )

            self.DAILY_REQUEST_COUNT += 1
            actual_total_tokens = response.usage_metadata.total_token_count
            self.CURRENT_MINUTE_TOKEN_COUNT += actual_total_tokens

            # Build dict from resp
            raw_text = response.text
            clean_json_str = raw_text.replace("```json", "").replace("```", "").strip()

            try:
                ai_result = json.loads(clean_json_str)
                validated_report = ReportModel(**ai_result)
                logger.info("AI result validated against schema successfully.")
            except json.JSONDecodeError:
                logger.error(f"Failed to parse JSON: {raw_text}")
                ai_result = {"status": "ERROR", "error": raw_text}
            except Exception as e:
                logger.error(f"AI response failed schema validation: {e}")
                ai_result = {"status": "ERROR", "error": f"Schema Validation Error"}

            resp_dict = {
                "result": ai_result,
                "status": ai_result.get('status'),
                "timestamp": time.time(),
                "token_used": response.usage_metadata.total_token_count if response.usage_metadata else 0
            }
            return resp_dict

        except APIError as e:
            logger.error(f"An error occurred during the API call: {e}")
            return {"status":"ERROR", "error": str(e)}
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return {"status":"ERROR", "error": str(e)}

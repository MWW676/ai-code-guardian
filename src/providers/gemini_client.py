import os
import json
import time
import logging
from dateutil import parser
from google import genai
from dotenv import load_dotenv
from google.genai import types
from google.genai.errors import APIError
from src.providers.llm_base import LLMProvider

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

class GeminiClient(LLMProvider):
    """Gemini openapi client to process llm prompts."""
    def __init__(self):
        # --- Define Known Limits ---
        self._MAX_RPD: int = 20
        self._MAX_TPM: int = 250_000
        # --- Global Tracking Variables ---
        self.DAILY_REQUEST_COUNT: int = 0
        self.LAST_REQUEST_TIME: float = time.time()
        self.CURRENT_MINUTE_TOKEN_COUNT: int = 0
        # --- Get API Key ---
        api_key = os.environ.get('GEMINI_API_KEY')
        if not api_key:
            raise EnvironmentError("GEMINI_API_KEY not found in environment.")
        # --- init client and model ---
        self.client = genai.Client(api_key=api_key)
        self.model_name = "gemini-2.5-flash"

    def check_and_reset_limits(self, contents: str, max_output_tokens: int):
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
        try:
            # Get the token count for the input prompt
            count_response = self.client.models.count_tokens(
                model=self.model_name,
                contents=[contents]
            )
            input_tokens = count_response.total_tokens
            potential_total_tokens = input_tokens + max_output_tokens

            # Check against TPM limit
            if self.CURRENT_MINUTE_TOKEN_COUNT + potential_total_tokens > self._MAX_TPM:
                logger.warning(f"TPM limit would be exceeded. Skipping API call.")
                return False

        except APIError as e:
            logger.error(f"Failed to count tokens: {e}. Skipping API call.")
            return False

        # 3. Always update the last request time
        self.LAST_REQUEST_TIME = now
        return True

    def safe_generate_content(self, contents: str, max_output_tokens: int = 5000):
        """Generates content through Gemini open api call."""
        check_result = self.check_and_reset_limits(contents=contents, max_output_tokens=max_output_tokens)
        assert check_result is True

        try:
            logger.info(f"Request {self.DAILY_REQUEST_COUNT + 1}/{self._MAX_RPD} initiated.")

            config_object = types.GenerateContentConfig(
                max_output_tokens=max_output_tokens  # Passes the integer value
            )
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=config_object
            )

            # 4. Update the global counters AFTER successful execution
            self.DAILY_REQUEST_COUNT += 1
            # The total tokens used for the call is the sum of input and output
            actual_total_tokens = response.usage_metadata.total_token_count
            self.CURRENT_MINUTE_TOKEN_COUNT += actual_total_tokens

            logger.info(f"[SUCCESS] Tokens used in this call: {actual_total_tokens}")
            logger.info(f"Response: {response.text[:50]}...")
            return response

        except APIError as e:
            logger.error(f"An error occurred during the API call: {e}")
            return None

    def analyze_diff(self, contents: str) -> dict:
        """Construct resp dict from Gemini api response."""
        response = self.safe_generate_content(contents=contents)

        # Build dict from resp
        http_raw_resp = json.loads(response.sdk_http_response.model_dump_json())
        date_string = http_raw_resp['headers'].get('date')

        resp_dict = {
            "result": response.text,
            "timestamp": parser.parse(date_string).timestamp(),
            "daily_request_raio": f"{self.DAILY_REQUEST_COUNT}/{self._MAX_RPD}"
        }
        return resp_dict

# if __name__ == "__main__":
#     load_dotenv()
#     content = "Explain how AI works in a few words"
#     provider = GeminiClient()
#     resp = provider.analyze_diff(contents=content)
#     print(f"Check in local run: \n{resp}")

import os
import json
import time
import logging
from google import genai
from google.genai import types
from google.genai.errors import APIError
from src.providers.llm_base import LLMProvider
from src.core.models import ReportModel

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

class GeminiClient(LLMProvider):
    SYSTEM_PROMPT = """
    You are a **Principal Software Engineer** and **Security Auditor** specializing in Python development and secure coding practices.
    Your singular task is to perform a code review based on the provided Git Diff and **output the final findings** as a single, contiguous JSON object.
    
    **[CODE REVIEW RUBRIC AND WEIGHTAGE START]**
    ### I. Code Correctness & Quality (Weight: 40%)
    * Logic & Functional Correctness
    * Error Handling & Robustness
    * Testability & Simplicity
    ### II. Maintainability & Readability (Weight: 30%)
    * Naming & Clarity
    * Documentation & Comments
    * Style & Idioms (PEP 8)
    ### III. Performance & Efficiency (Weight: 10%)
    * Algorithmic Efficiency
    * Resource Use
    ### IV. Security & Vulnerabilities (Weight: 20%)
    * Input Validation & Sanitization
    * Sensitive Data Handling
    * Dependency Changes
    **[CODE REVIEW RUBRIC AND WEIGHTAGE END]**
    """

    def __init__(self):
        api_key = os.environ.get('GEMINI_API_KEY')
        if not api_key:
            raise EnvironmentError("GEMINI_API_KEY not found in environment.")
        self.client = genai.Client(api_key=api_key)
        self.model_name = "gemini-2.5-flash-lite"

        # --- Define Known Limits ---
        self._MAX_RPD: int = 20
        self._MAX_TPM: int = 250_000
        self._max_output_tokens = 6000
        # --- Global Tracking Variables ---
        # TODO: Implement DynamoDB for persistent rate limiting in Lambda
        self.DAILY_REQUEST_COUNT: int = 0
        self.LAST_REQUEST_TIME: float = time.time()
        self.CURRENT_MINUTE_TOKEN_COUNT: int = 0

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

    def generate_prompt(self, contents: str) -> str:
        # Construct prompt
        review_schema_dict = ReportModel.model_json_schema()
        prompt = f"""
        --- START SYSTEM INSTRUCTION ---
        {self.SYSTEM_PROMPT}
        
        --- OUTPUT FORMAT INSTRUCTION ---

        1.  **Strict Adherence:** Your complete output must be a **single, valid JSON object** that conforms exactly to the structure defined by the `ReportModel` schema provided between the tags below.
        2.  **Constraint:** You **MUST NOT** include any part of the JSON Schema definition itself, any surrounding prose, explanations, or Markdown fences (like ```json).
        3.  **Target Object:** Start your response directly with the opening curly brace of the `ReportModel` object.
        
        [JSON SCHEMA BEGIN]
        {json.dumps(review_schema_dict, indent=2)}
        [JSON SCHEMA END]
        --- END SYSTEM INSTRUCTION ---

        Please analyze the following code diff and provide the completed ReportModel JSON object:
        [GIT DIFF CONTENT START]
        {contents}
        [GIT DIFF CONTENT END]
        """
        return prompt

    def analyze_diff(self, contents: str) -> dict:
        """Generates content through Gemini open api call."""
        final_prompt = self.generate_prompt(contents=contents)
        if not self.check_and_reset_limits(contents=final_prompt):
            logger.warning("Limit or token quota check failed.")
            return {"status":"SKIPPED", "reason": "Rate/Token limit exceeded."}

        try:
            logger.info(f"Evaluating code diff with model: {self.model_name}...")
            config_object = types.GenerateContentConfig(
                max_output_tokens=self._max_output_tokens,
                response_mime_type="application/json"
            )
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=contents,
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
            except json.JSONDecodeError:
                logger.error(f"Failed to parse JSON: {raw_text}")
                ai_result = {"status": "ERROR", "error": raw_text}

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

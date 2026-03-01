import multiprocessing
import logging
import os
from dotenv import load_dotenv
from src.utils.config_manager import config
from src.providers.gemini_client import GeminiClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logeer = logging.getLogger("Calibration")

def run_single_audit(policy_name):
    """Worker function to run a single review."""
    client = GeminiClient(api_key=os.getenv("GEMINI_API_KEY"), policy_name=policy_name)
    dummy_diff = "def add(a, b): return a + b"

    logeer.info(f"Process starting review with policy: {policy_name}")
    result = client.analyze_diff(dummy_diff)
    return policy_name, result

if __name__ == "__main__":
    policies_to_test = config.available_policies
    load_dotenv()

    with multiprocessing.Pool(processes=len(policies_to_test)) as pool:
        results = pool.map(run_single_audit, policies_to_test)

    for policy, resp in results:
        status = resp.get("status")
        score = resp["result"].get("policy_alignment_score", 0)
        logeer.info(f"Audit Result - Policy: {policy} | Status: {status} | Alignment: {score}%")

import os
import json
import logging
import yaml
from src.providers.gemini_client import GeminiClient
from src.utils.config_manager import config
from dotenv import load_dotenv
from tests import TEST_DATA_DIR

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("HallucinationAudit")

def run_hallucination_audit(api_key):
    file_path = TEST_DATA_DIR / "golden_set.yaml"
    with open(file_path, "r") as f:
        golden_set = yaml.safe_load(f)

    traps = [item for item in golden_set if "TRAP" in item['id']]
    if not traps:
        logger.error(f"No TRAP cases found at {file_path}.")
        return

    personas = config.available_policies
    hallucination_results = []

    for trap in traps:
        for persona in personas:
            logger.info(f"Auditing Trap {trap['id']} with Persona: {persona}")
            client = GeminiClient(api_key=api_key, policy_name=persona)

            for i in range(2):
                resp = client.analyze_diff(trap['diff'])
                findings = resp['result'].get('comments', [])
                risk_score = resp['result'].get('risk_score', 0)

                is_hallucination = len(findings) > 0 or risk_score > 0
                hallucination_results.append({
                    "trap_id": trap['id'],
                    "persona": persona,
                    "is_hallucination": is_hallucination,
                    "hallucination_issue": findings[0].get('description') if findings else "None"
                })

    result_file_path = TEST_DATA_DIR / "hallucination_results.json"
    with open(result_file_path, "w") as f:
        json.dump(hallucination_results, f, indent=4)

    logger.info("Hallucination Audit complete.")

if __name__ == "__main__":
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    run_hallucination_audit(api_key=api_key)

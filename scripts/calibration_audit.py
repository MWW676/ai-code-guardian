import multiprocessing
import logging
import os
import json
import yaml
from dotenv import load_dotenv
from tests import TEST_DATA_DIR
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

def run_benchmark_iteration(task):
    policy, diff_id, diff_content, iteration, api_key = task
    client = GeminiClient(api_key=api_key, policy_name=policy)
    resp = client.analyze_diff(diff_content)

    return {
        "diff_id": diff_id,
        "policy": policy,
        "iteration": iteration,
        "risk_score": resp["result"].get("risk_score"),
        "alignment": resp["result"].get("policy_alignment_score"),
        "diff_hash": resp["metadata"].get("diff_hash")
    }

if __name__ == "__main__":
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    policies_to_test = config.available_policies
    # # Same code diff & Different persona
    # with multiprocessing.Pool(processes=len(policies_to_test)) as pool:
    #     results = pool.map(run_single_audit, policies_to_test)
    #
    # for policy, resp in results:
    #     status = resp.get("status")
    #     score = resp["result"].get("policy_alignment_score", 0)
    #     logeer.info(f"Audit Result - Policy: {policy} | Status: {status} | Alignment: {score}%")

    # Same code diff, same persona
    file_path = TEST_DATA_DIR / "golden_set.yaml"
    with open(file_path, "r") as f:
        golden_set = yaml.safe_load(f)

    tasks, MAX_ITER_COUNT = [], 2
    for diff in golden_set:
        for i in range(MAX_ITER_COUNT):
            tasks.append((policies_to_test[0], diff['id'], diff['diff'], i, api_key))

    with multiprocessing.Pool(processes=MAX_ITER_COUNT) as pool:
        results = pool.map(run_benchmark_iteration, tasks)

    policy = tasks[0][0]
    result_file_path = TEST_DATA_DIR / f"telemetry_benchmarks_{policy}.json"
    with open(result_file_path, "w") as f:
        json.dump(results, f, indent=2)

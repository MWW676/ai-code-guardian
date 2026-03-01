import json
import statistics
from collections import defaultdict
import logging, sys
from tests import TEST_DATA_DIR
from src.providers.dynamodb_reader import DynamodbReader
from src.core.models import ReportModel
from pydantic import ValidationError

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler(sys.stdout)
logger.addHandler(console_handler)

class DriftAnalyzer:
    @staticmethod
    def calculate_stability(json_file):
        """Analyzes drift over SAME code / SAME persona."""
        with open(json_file, "r") as f:
            data = json.load(f)

        groups = defaultdict(list)
        for r in data:
            groups[f"{r['diff_id']} | {r['policy']}"].append(r['risk_score'])

        logger.info("--- STABILITY ANALYSIS (Benchmark) ---")
        stability_summary = []

        for key, scores in groups.items():
            std_dev = statistics.stdev(scores) if len(scores) > 1 else 0
            avg_score = sum(scores) / len(scores)
            result = {
                "target": key,
                "avg_score": round(avg_score, 2),
                "drift": round(std_dev, 2)
            }
            stability_summary.append(result)
            logger.info(f"Target {key} | Avg: {avg_score:.2f} | Drift: {std_dev:.2f}")

        result_file_path = TEST_DATA_DIR / "stability_results.json"
        with open(result_file_path, "w") as f:
            json.dump(stability_summary, f, indent=4)

    @staticmethod
    def calculate_performance_distribution(table_name):
        """Analyzes score distribution across DIFFERENT personas from Prod."""
        reader = DynamodbReader(table_name=table_name)
        production_data = reader.fetch_all_telemetry()
        if not production_data:
            logger.warning("No production data found.")
            return

        policy_scores = defaultdict(list)
        for r in production_data:
            try:
                ReportModel(**r['result'])
                policy = r.get('metadata', {}).get('policy', 'UNKNOWN')
                score = r.get('result', {}).get('risk_score', 0)
                policy_scores[policy].append(score)
            except (ValidationError, KeyError) as e:
                logger.warning(f"Skipping incompatible/old record: {r.get('record_id', 'unknown')}")

        logger.info("\n--- PERFORMANCE DISTRIBUTION (Production) ---")
        dist_summary = []

        for policy, scores in policy_scores.items():
            result = {
                "policy": policy,
                "mean": round(statistics.mean(scores), 2),
                "min": min(scores),
                "max": max(scores),
                "sample_size": len(scores)
            }
            dist_summary.append(result)
            logger.info(f"Policy: {policy} | Mean: {result['mean']} | Sample Size: {result['sample_size']}")

        result_file_path = TEST_DATA_DIR / "prod_snapshot.json"
        with open(result_file_path, "w") as f:
            json.dump(dist_summary, f, indent=4)


if __name__ == "__main__":
    analyzer = DriftAnalyzer()
    benchmark_data_file = TEST_DATA_DIR / "telemetry_benchmarks.json"
    if benchmark_data_file.exists():
        analyzer.calculate_stability(benchmark_data_file)

    # table_name = 'CodeGuardian-Logs'
    # analyzer.calculate_performance_distribution(table_name=table_name)

import json
import statistics
from collections import defaultdict
import logging, sys
from tests import TEST_DATA_DIR
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
            groups[f"{r['diff_id']}_{r['policy']}"].append(r['risk_score'])

        logger.info("--- STABILITY ANALYSIS (Benchmark) ---")
        for key, scores in groups.items():
            std_dev = statistics.stdev(scores) if len(scores) > 1 else 0
            logger.info(f"Target {key} | Avg score {sum(scores)/len(scores)} | Drift (StdDev): {std_dev:.2f}")

    @staticmethod
    def calculate_performance_distribution(production_data):
        """Analyzes score distribution across DIFFERENT personas from Prod."""
        policy_scores = defaultdict(list)
        for r in production_data:
            policy_scores[r['policy']].append(r['risk_score'])

        logger.info("\n--- PERFORMANCE DISTRIBUTION (Production) ---")
        for policy, scores in policy_scores.items():
            logger.info(f"Policy: {policy} | Mean: {statistics.mean(scores):.2f} | Range: {min(scores)}-{max(scores)}")

if __name__ == "__main__":
    benchmark_data_file = TEST_DATA_DIR / "telemetry_benchmarks.json"
    analyzer = DriftAnalyzer()
    analyzer.calculate_stability(benchmark_data_file)

from flask import Flask, render_template_string
import json
from pathlib import Path

app = Flask(__name__)

# Paths
BASE_PATH = Path(__file__).parent
STABILITY_FILE = BASE_PATH / "tests" / "test_data" / "stability_results.json"
PROD_FILE = BASE_PATH / "tests" / "test_data" / "prod_snapshot.json"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>AI Guardian Dashboard</title>
    <style>
        body { font-family: sans-serif; padding: 40px; background: #f4f4f9; }
        .card { background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        h1 { color: #2c3e50; }
        .metric { display: inline-block; margin-right: 30px; }
        .value { font-size: 24px; font-weight: bold; color: #3498db; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
    </style>
</head>
<body>
    <h1>🛡️ AI-Code-Guardian Governance</h1>

    <div class="card">
        <h2>1. Stability Benchmark</h2>
        {% for item in stability %}
        <div class="metric">
            <div>{{ item.target }}</div>
            <div class="value">{{ item.avg_score }}% (Drift: {{ item.drift }})</div>
        </div>
        {% endfor %}
    </div>

    <div class="card">
        <h2>2. Production Snapshots</h2>
        <table>
            <tr><th>Policy</th><th>Mean Score</th><th>Samples</th></tr>
            {% for item in prod %}
            <tr>
                <td>{{ item.policy }}</td>
                <td>{{ item.mean }}</td>
                <td>{{ item.sample_size }}</td>
            </tr>
            {% endfor %}
        </table>
    </div>
</body>
</html>
"""


def load_data(path):
    if path.exists():
        with open(path, 'r') as f:
            return json.load(f)
    return []


@app.route('/')
def home():
    stability = load_data(STABILITY_FILE)
    prod = load_data(PROD_FILE)
    return render_template_string(HTML_TEMPLATE, stability=stability, prod=prod)


if __name__ == '__main__':
    # Running on port 5001 to avoid conflicts
    print("Dashboard starting at http://127.0.0.1:5001")
    app.run(port=5001, debug=False)
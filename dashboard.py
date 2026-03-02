import streamlit as st
import json
import time
from pathlib import Path

# --- Configuration & Pathing ---
BASE_PATH = Path(__file__).parent
STABILITY_FILE = BASE_PATH / "tests" / "test_data" / "stability_results.json"
PROD_FILE = BASE_PATH / "tests" / "test_data" / "prod_snapshot.json"

st.set_page_config(page_title="AI-Guardian Governance Dashboard", page_icon="🛡️")


# --- DATA LOADING ---
def load_json_data(file_path):
    try:
        if not file_path.exists():
            return None
        with open(file_path, "r") as f:
            return json.load(f)
    except Exception:
        return None


# --- UI START ---
st.title("🛡️ AI-Code-Guardian: Governance Dashboard")
st.write(f"**Last Sync:** {time.strftime('%Y-%m-%d %H:%M:%S')}")
st.divider()

# --- SECTION 1: Stability Benchmark ---
st.header("1. Model Stability (Golden Set)")
st.caption("Lower drift indicates higher AI consistency.")

stability_data = load_json_data(STABILITY_FILE)

if stability_data:
    # Use st.metric vertically for stability
    for item in stability_data:
        st.metric(
            label=f"Lens: {item['target']}",
            value=f"{item['avg_score']}% Accuracy",
            delta=f"{item['drift']} Drift",
            delta_color="inverse" if item['drift'] > 5 else "normal"
        )

    # with st.expander("Show Benchmark Raw Data"):
    #     st.write(stability_data)
else:
    st.warning("Benchmark data not found.")

st.divider()

# --- SECTION 2: Production Performance ---
st.header("2. Production Persona Analysis")
st.caption("Performance distribution across rotated policies.")

prod_data = load_json_data(PROD_FILE)

if prod_data:
    for item in prod_data:
        # Simplified metrics for production
        st.write(f"### Policy: {item['policy']}")
        st.write(f"**Mean Score:** {item['mean']} | **Sample Size:** {item['sample_size']}")
        st.progress(min(int(item['mean']), 100))

    # with st.expander("Show Production Raw Data"):
    #     st.write(prod_data)
else:
    st.warning("Production data not found.")

st.divider()
st.info("System Note: Optimized for Legacy macOS Stability.")
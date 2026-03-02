import streamlit as st
import json
import time
from pathlib import Path

# --- Configuration & Pathing ---
BASE_PATH = Path(__file__).parent
STABILITY_FILE = BASE_PATH / "tests" / "test_data" / "stability_results.json"
PROD_FILE = BASE_PATH / "tests" / "test_data" / "prod_snapshot.json"
HALLUCINATION_FILE = BASE_PATH / "tests" / "test_data" / "hallucination_results.json"

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
    for item in stability_data:
        st.metric(
            label=f"Lens: {item['target']}",
            value=f"{item['avg_score']}% Accuracy",
            delta=f"{item['drift']} Drift",
            delta_color="inverse" if item['drift'] > 5 else "normal"
        )
else:
    st.warning("Benchmark data not found.")

st.divider()

# --- SECTION 2: Production Performance ---
st.header("2. Production Persona Analysis")
st.caption("Performance distribution across rotated policies.")

prod_data = load_json_data(PROD_FILE)

if prod_data:
    for item in prod_data:
        st.write(f"### Policy: {item['policy']}")
        st.write(f"**Mean Score:** {item['mean']} | **Sample Size:** {item['sample_size']}")
        st.progress(min(int(item['mean']), 100))
else:
    st.warning("Production data not found.")

st.divider()

# --- SECTION 3: Hallucination & Persona Bias ---
st.header("3. Hallucination & Persona Bias")
st.info("AI was fed 'Ground Truth' perfect code. Any findings below are Persona Hallucinations.")

hallucination_data = load_json_data(HALLUCINATION_FILE)

if hallucination_data:
    for item in hallucination_data:
        # Create a visual indicator for Hallucination
        status_icon = "⚠️" if item['is_hallucination'] else "✅"
        status_label = "HALLUCINATED" if item['is_hallucination'] else "STABLE"
        color = "red" if item['is_hallucination'] else "green"

        # Display the result
        st.markdown(f"### {status_icon} {item['persona']}: :{color}[{status_label}]")

        # Show the hallucinated text
        if item['is_hallucination']:
            st.warning(f"**Observation:** {item['hallucination_issue']}")
        else:
            st.success("AI correctly identified code as optimal.")

        st.write("---")
else:
    st.warning("Hallucination results not found. Run 'hallucination_auditor.py' first.")

# st.divider()
# st.info("System Note: Optimized for Legacy macOS Stability. No heavy C++ dependencies active.")
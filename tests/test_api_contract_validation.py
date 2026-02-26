from pathlib import Path
import os
import json
import pytest
from jsonschema import validate, ValidationError

def test_api_contract_validation():
    # file_path = os.path.join(os.path.dirname(__file__), "test_data/schema_test_cases_v2.json")
    base_path = Path(__file__).parent
    file_path = base_path / 'test_data' / 'schema_test_cases_v2.json'
    with open(file_path, 'r') as f:
        schema = json.load(f)

    dirty_api_response = {
        "status": "PASS",
        "risk_score": 999
    }
    with pytest.raises(ValidationError) as exc_info:
        validate(instance=dirty_api_response, schema=schema)

    assert "999 is greater than the maximum of 100" in str(exc_info.value)

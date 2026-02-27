from pathlib import Path
import json
import pytest
from jsonschema import validate, ValidationError
from tests import TEST_DATA_DIR

def test_api_contract_validation():
    file_path = TEST_DATA_DIR / 'schema_test_cases_v2.json'
    with open(file_path, 'r') as f:
        schema = json.load(f)

    dirty_api_response = {
        "status": "PASS",
        "risk_score": 999
    }
    with pytest.raises(ValidationError) as exc_info:
        validate(instance=dirty_api_response, schema=schema)

    assert "999 is greater than the maximum of 100" in str(exc_info.value)

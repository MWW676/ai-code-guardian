import pytest
import yaml
import os
from pydantic import ValidationError
from src.core.models import ReportModel

def load_schema_cases():
    file_path = os.path.join(os.path.dirname(__file__), "test_data/schema_test_cases.yaml")
    with open(file_path, 'r') as f:
        return yaml.safe_load(f)

@pytest.mark.parametrize("case", load_schema_cases())
def test_ai_output_schema_validation(case):
    if case['expected_valid']:
        model = ReportModel(**case['payload'])
        assert model.risk_score == case['payload']['risk_score']
    else:
        with pytest.raises(ValidationError) as exc_info:
            ReportModel(**case['payload'])
        assert case['error_snippet'] in str(exc_info.value)
        print(f"\n✅ Corrected caught expected error: {case['name']}")
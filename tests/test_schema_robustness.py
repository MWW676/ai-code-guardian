import pytest
import yaml
from pydantic import ValidationError
from src.core.models import ReportModel
from tests import logger, TEST_DATA_DIR

def load_schema_cases():
    file_path = TEST_DATA_DIR / "schema_test_cases.yaml"
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
        logger.info(f"\n✅ Corrected caught expected error: {case['name']}")
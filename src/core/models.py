from enum import Enum
from pydantic import BaseModel, Field

class ReviewStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    NEEDS_ATTENTION = "NEEDS_ATTENTION"

class Severity(str, Enum):
    CRITICAL = "CRITICAL"
    MINOR = "MINOR"
    INFO = "INFO"

class CheckPoint(str, Enum):
    # I. Code Correctness & Quality
    LOGIC_CORRECTNESS = "Logic & Functional Correctness"
    ERROR_HANDLING = "Error Handling & Robustness"
    TESTABILITY = "Testability & Simplicity"
    # II. Maintainability & Readability
    NAMING_CLARITY = "Naming & Clarity"
    DOCUMENTATION = "Documentation & Comments"
    STYLE_IDIOMS = "Style & Idioms (PEP 8/Best Practices)"
    # III. Performance & Efficiency
    ALGORITHMIC_EFFICIENCY = "Algorithmic Efficiency"
    RESOURCE_USE = "Resource Use"
    # IV. Security & Vulnerabilities
    INPUT_VALIDATION_SANITIZATION = "Input Validation & Sanitization"
    SENSITIVE_DATA_HANDLING = "Sensitive Data Handling"
    DEPENDENCY_VULNERABILITY = "Dependency Changes"

class CommentModel(BaseModel):
    severity: Severity = Field(description="The risk level of the finding.")
    # checkpoint: CheckPoint = Field(description="The specific item from the Code Review Rubric this issue falls under.")
    file: str = Field(description="The file path of the code change.")
    line: str = Field(description="The line number range where the issue was found.")
    description: str = Field(description="A detailed explanation of the issue.")
    suggestion: str = Field(description="A concrete fix suggestion.")

class ReportModel(BaseModel):
    status: ReviewStatus = Field(description="The overall status of the code review.")
    risk_score: int = Field(ge=0, le=100, description="Overall risk score from 0 to 100.")
    comments: list[CommentModel] = Field(description="A list of specific issues found in the diff.")

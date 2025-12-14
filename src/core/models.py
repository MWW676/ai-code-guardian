
from enum import Enum
from pydantic import BaseModel, Field

# --- NEW ENUMS ---
class IssueCategory(str, Enum):
    CORRECTNESS = "CORRECTNESS"
    MAINTAINABILITY = "MAINTAINABILITY"
    PERFORMANCE = "PERFORMANCE"
    SECURITY = "SECURITY"

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

# --- EXISTING ENUMS (with minor descriptions added) ---
class ReviewStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    NEEDS_ATTENTION = "NEEDS_ATTENTION"

class Severity(str, Enum):
    CRITICAL = "CRITICAL" # Requires immediate fix before merge.
    MINOR = "MINOR"      # Should be fixed before merge, but not a blocker.
    INFO = "INFO"        # Suggestion or best practice violation.

# --- UPDATED CommentModel ---
class CommentModel(BaseModel):
    category: IssueCategory = Field(description="The high-level category of the issue.")
    checkpoint: CheckPoint = Field(description="The specific item from the Code Review Rubric this issue falls under.")
    severity: Severity = Field(description="The risk level of the finding.")
    file: str = Field(description="The file path of the code change.")
    line: str = Field(description="The line number where the issue was found (use 'N/A' for file-wide issues).")
    description: str = Field(description="A detailed explanation of the issue.")
    suggestion: str = Field(description="A concrete fix suggestion or best practice to adopt.")

# --- ReportModel remains the same, but imports the new CommentModel ---
class ReportModel(BaseModel):
    status: ReviewStatus = Field(description="The overall status of the code review.")
    risk_score: int = Field(ge=0, le=100, description="Overall risk score from 0 to 100.")
    # Add explicit default [] to ensure clean JSON schema generation
    comments: list[CommentModel] = Field(
        default=[], # <-- This resolves the warning by providing a serializable default
        description="A list of specific issues found in the diff."
    )
from src.core.models import ReviewStatus, Severity, IssueCategory

status_emoji = {
    ReviewStatus.PASS: "✅",
    ReviewStatus.FAIL: "❌",
    ReviewStatus.NEEDS_ATTENTION: "⚠️"
}

severity_emoji = {
    Severity.CRITICAL: "🔴",
    Severity.MINOR: "🟠",
    Severity.INFO: "🟡"
}

category_emoji = {
    IssueCategory.CORRECTNESS: "🚨",
    IssueCategory.MAINTAINABILITY: "🛠",
    IssueCategory.PERFORMANCE: "⏳",
    IssueCategory.SECURITY: "⛔"
}
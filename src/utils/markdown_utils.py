import logging
from src.utils.emoji_maps import *

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def format_report_to_markdown(report_data: dict) -> str:
    status = report_data.get("status")
    result = report_data.get("result")
    if not status or not result:
        logger.warning("Report data missing status/report body.")
        return "ERROR"
    status_enum = ReviewStatus(status)

    score = result.get('risk_score')
    comments = result.get('comments')

    report_title = f"# 🤖AI Code Review Report\n"
    report_summary = f"## 📊Summary\n- **Overall Status**:{status_emoji.get(status_enum, "❓")}{status}\n- **Risk Score**: {score}/100\n"
    detail_findings = "## 🔍Detailed Findings\n"

    details = []
    for comment in comments:
        severity = comment.get('severity', 'N/A')
        category = comment.get('category', 'N/A')
        severity_enum = Severity(severity)
        category_enum = IssueCategory(category)
        detail = (f"### {severity_emoji.get(severity_enum, "❓")}[{severity}] - {comment.get('file', 'N/A')}\n- **Location**: Lines {comment.get('line', 'N/A')}\n- **Category**: {category_emoji.get(category_enum, "❓")}{category}\n"
                  f"- **Checkpoint**: {comment.get('checkpoint', 'N/A')}\n- **Description**: {comment.get('description', 'N/A')}\n- **💡Suggestion**: {comment.get('suggestion', 'N/A')}\n")
        details.append(detail)

    report = report_title + report_summary + detail_findings + "\n".join(details)
    return report

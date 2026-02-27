from jinja2 import Template
from pathlib import Path

def render_review_prompt(policy_name, persona_instruction, schema_str):
    template_path = Path(__file__).parent.parent / "prompts" / "review_template.md"

    with open(template_path, "r", encoding="utf-8") as f:
        template = Template(f.read())

    return template.render(
        policy_name=policy_name,
        persona_instruction=persona_instruction,
        schema_str=schema_str
    )

def render_diff_prompt(diff_content):
    template_path = Path(__file__).parent.parent / "prompts" / "diff_analysis_template.md"

    with open(template_path, "r", encoding="utf-8") as f:
        template = Template(f.read())

    return template.render(contents=diff_content)
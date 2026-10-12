from jinja2 import Template
from pathlib import Path

def render_system_instrcution_prompt(policy_name, persona_instruction, schema_str):
    template_path = Path(__file__).parent.parent / "prompts" / "system_instruction_template.md"

    with open(template_path, "r", encoding="utf-8") as f:
        template = Template(f.read())

    return template.render(
        policy_name=policy_name,
        persona_instruction=persona_instruction,
        schema_str=schema_str
    )

def render_user_message_prompt(diff_content):
    template_path = Path(__file__).parent.parent / "prompts" / "user_message_template.md"

    with open(template_path, "r", encoding="utf-8") as f:
        template = Template(f.read())

    return template.render(contents=diff_content)
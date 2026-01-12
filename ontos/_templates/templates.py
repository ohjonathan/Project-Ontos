"""
Canonical template loader - Single source of truth for all templates.
Prevents drift between user-mode starters and contributor-mode references.
"""
import os

TEMPLATES_DIR = os.path.dirname(os.path.abspath(__file__))


def load_template(name: str) -> str:
    """Load template from shipped reference file."""
    template_path = os.path.join(TEMPLATES_DIR, name)
    if os.path.exists(template_path):
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()
    raise FileNotFoundError(f"Template not found: {template_path}")


def get_decision_history_template() -> str:
    """Get decision_history.md template."""
    return load_template('decision_history_template.md')


def get_common_concepts_template() -> str:
    """Get Common_Concepts.md template."""
    return load_template('common_concepts_template.md')

"""LLM-powered engineering analysis engine."""

from __future__ import annotations

import sys

import anthropic

from archetype.models import RequirementsAnalysis, TradeStudy
from archetype.parsing import extract_json_text

ANALYSIS_SYSTEM = """You are an experienced engineering design consultant. You analyze requirements
for physical products and systems — mechanical parts, assemblies, structures, thermal systems, etc.

When given engineering requirements, you:
1. Identify the key design drivers (weight, cost, strength, thermal performance,
   manufacturability, etc.)
2. Assign relative importance weights that sum to 1.0
3. Extract target values and constraints from the requirements

Be specific and quantitative where the requirements allow. Use standard engineering units."""

CONCEPTS_SYSTEM = """You are an experienced engineering design consultant generating design concept
variants for a trade study. For each concept:
1. Propose a distinct, plausible design approach
2. Score it 0-10 against each design driver (10 = fully meets or exceeds the target)
3. Provide brief rationale for each score

Generate diverse concepts — don't just vary one parameter. Think about different materials,
geometries, manufacturing methods, or architectural approaches. Be realistic about tradeoffs:
no concept should score 10 on everything."""


def _get_client(api_key: str | None = None) -> anthropic.Anthropic:
    """Create an Anthropic client, falling back to env var."""
    try:
        return anthropic.Anthropic(api_key=api_key) if api_key else anthropic.Anthropic()
    except TypeError:
        print(
            "Error: No API key found. Set ANTHROPIC_API_KEY or pass --api-key.",
            file=sys.stderr,
        )
        sys.exit(1)


def analyze_requirements(
    requirements: str,
    api_key: str | None = None,
    model: str = "claude-sonnet-4-20250514",
) -> RequirementsAnalysis:
    """Decompose raw requirements text into structured design drivers."""
    client = _get_client(api_key)

    response = client.messages.create(
        model=model,
        max_tokens=2000,
        system=ANALYSIS_SYSTEM,
        messages=[
            {
                "role": "user",
                "content": (
                    f"Analyze these engineering requirements and extract the key design "
                    f"drivers with importance weights.\n\n"
                    f"Requirements:\n{requirements}\n\n"
                    f"Respond with valid JSON matching this schema:\n"
                    f"{RequirementsAnalysis.model_json_schema()}"
                ),
            }
        ],
    )

    block = response.content[0]
    if not hasattr(block, "text"):
        raise ValueError("Expected text response from model")
    text = extract_json_text(block.text)
    return RequirementsAnalysis.model_validate_json(text)


def generate_concepts(
    requirements: str,
    analysis: RequirementsAnalysis,
    num_concepts: int = 4,
    api_key: str | None = None,
    model: str = "claude-sonnet-4-20250514",
) -> TradeStudy:
    """Generate design concepts and score them against the design drivers."""
    client = _get_client(api_key)

    driver_names = [d.name for d in analysis.drivers]
    driver_summary = "\n".join(
        f"- {d.name} (weight: {d.weight:.2f}): {d.description} — target: {d.target}"
        for d in analysis.drivers
    )

    response = client.messages.create(
        model=model,
        max_tokens=4000,
        system=CONCEPTS_SYSTEM,
        messages=[
            {
                "role": "user",
                "content": (
                    f"Generate {num_concepts} design concepts for this engineering problem.\n\n"
                    f"Requirements:\n{requirements}\n\n"
                    f"Design Drivers:\n{driver_summary}\n\n"
                    f"Score each concept on these drivers (0-10): {driver_names}\n\n"
                    f"The 'scores' dict keys must exactly match: {driver_names}\n"
                    f"The 'rationale' dict keys must exactly match: {driver_names}\n\n"
                    f"Respond with valid JSON matching this schema:\n"
                    f"{TradeStudy.model_json_schema()}"
                ),
            }
        ],
    )

    block = response.content[0]
    if not hasattr(block, "text"):
        raise ValueError("Expected text response from model")
    text = extract_json_text(block.text)
    return TradeStudy.model_validate_json(text)

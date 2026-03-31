"""Response parsing utilities for LLM output."""

from __future__ import annotations

__all__ = ["extract_json_text"]


def extract_json_text(raw: str) -> str:
    """Extract JSON content from a string, stripping markdown fences if present."""
    stripped = raw.strip()
    if stripped.startswith("```"):
        lines = stripped.split("\n")
        lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        stripped = "\n".join(lines)
    return stripped

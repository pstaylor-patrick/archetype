"""Pydantic models for structured LLM output."""

from __future__ import annotations

__all__ = ["DesignConcept", "DesignDriver", "RequirementsAnalysis", "TradeStudy"]

from pydantic import BaseModel, Field


class DesignDriver(BaseModel):
    """A key design requirement extracted from the spec."""

    name: str = Field(description="Short name for the design driver (e.g., 'Weight', 'Cost')")
    description: str = Field(description="What this driver means in context")
    unit: str = Field(description="Unit of measure or 'qualitative' if not quantifiable")
    target: str = Field(description="Target value or constraint from the requirements")
    weight: float = Field(
        ge=0.0,
        le=1.0,
        description="Relative importance weight (0-1), all weights should sum to 1.0",
    )


class DesignConcept(BaseModel):
    """A proposed design concept variant."""

    name: str = Field(description="Short descriptive name for this concept")
    approach: str = Field(description="Brief description of the design approach")
    scores: dict[str, float] = Field(
        description="Score for each design driver (0-10 scale, 10 = best)"
    )
    rationale: dict[str, str] = Field(
        description="Brief rationale for each score, keyed by driver name"
    )


class RequirementsAnalysis(BaseModel):
    """Structured decomposition of engineering requirements."""

    summary: str = Field(description="One-sentence summary of the design problem")
    drivers: list[DesignDriver] = Field(description="Extracted design drivers with weights")


class TradeStudy(BaseModel):
    """Complete trade study with concepts scored against drivers."""

    concepts: list[DesignConcept] = Field(description="Proposed design concepts")
    recommendation: str = Field(description="Which concept is recommended and why")

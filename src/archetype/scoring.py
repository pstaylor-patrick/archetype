"""Weighted scoring and ranking logic for design tradeoff analysis."""

from __future__ import annotations

__all__ = ["score_color", "weighted_score", "rank_concepts"]

from archetype.models import DesignConcept, RequirementsAnalysis


def score_color(score: float) -> str:
    """Map a 0-10 score to a Rich color name."""
    if score >= 8:
        return "green"
    if score >= 6:
        return "yellow"
    if score >= 4:
        return "bright_black"
    return "red"


def weighted_score(concept_scores: dict[str, float], analysis: RequirementsAnalysis) -> float:
    """Calculate the weighted composite score for a concept against design drivers."""
    total = 0.0
    for driver in analysis.drivers:
        total += concept_scores.get(driver.name, 0) * driver.weight
    return total


def rank_concepts(
    concepts: list[DesignConcept], analysis: RequirementsAnalysis
) -> list[tuple[DesignConcept, float]]:
    """Rank concepts by weighted score, descending."""
    scored = [(c, weighted_score(c.scores, analysis)) for c in concepts]
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored

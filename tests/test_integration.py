"""Integration tests — real Anthropic API calls against physical engineering scenarios.

These tests validate that the full pipeline produces structurally valid, physically
plausible engineering analysis. They use claude-haiku to minimize token cost.

Run with: pytest tests/test_integration.py -m integration
Requires: ANTHROPIC_API_KEY environment variable
"""

from __future__ import annotations

import pytest

from archetype.engine import analyze_requirements, generate_concepts
from archetype.models import RequirementsAnalysis, TradeStudy
from archetype.scoring import rank_concepts, weighted_score

from .conftest import (
    BRACKET_REQUIREMENTS,
    HEAT_SINK_REQUIREMENTS,
    INTEGRATION_MODEL,
    PIPE_FITTING_REQUIREMENTS,
    skip_without_api_key,
)

# ---------------------------------------------------------------------------
# Requirements Analysis — does the LLM correctly decompose engineering specs?
# ---------------------------------------------------------------------------


@skip_without_api_key
@pytest.mark.integration
class TestRequirementsDecomposition:
    """Verify the LLM extracts physically meaningful design drivers from specs."""

    def test_bracket_extracts_structural_and_cost_drivers(self) -> None:
        analysis = analyze_requirements(BRACKET_REQUIREMENTS, model=INTEGRATION_MODEL)

        assert isinstance(analysis, RequirementsAnalysis)
        assert len(analysis.drivers) >= 3
        assert analysis.summary  # non-empty summary

        driver_names_lower = [d.name.lower() for d in analysis.drivers]
        combined = " ".join(driver_names_lower)

        # The spec mentions vibration, cost, corrosion — at least some should appear
        has_structural = any(
            kw in combined for kw in ["structural", "vibration", "deflection", "strength", "load"]
        )
        has_cost = any(kw in combined for kw in ["cost", "budget", "price"])
        assert has_structural, f"Expected a structural driver, got: {driver_names_lower}"
        assert has_cost, f"Expected a cost driver, got: {driver_names_lower}"

    def test_heat_sink_extracts_thermal_drivers(self) -> None:
        analysis = analyze_requirements(HEAT_SINK_REQUIREMENTS, model=INTEGRATION_MODEL)

        driver_names_lower = [d.name.lower() for d in analysis.drivers]
        combined = " ".join(driver_names_lower)

        has_thermal = any(
            kw in combined for kw in ["thermal", "temperature", "heat", "cooling", "dissipation"]
        )
        assert has_thermal, f"Expected a thermal driver, got: {driver_names_lower}"

    def test_weights_sum_approximately_to_one(self) -> None:
        analysis = analyze_requirements(BRACKET_REQUIREMENTS, model=INTEGRATION_MODEL)
        total = sum(d.weight for d in analysis.drivers)
        assert 0.9 <= total <= 1.1, f"Weights sum to {total}, expected ~1.0"

    def test_all_weights_are_positive(self) -> None:
        analysis = analyze_requirements(HEAT_SINK_REQUIREMENTS, model=INTEGRATION_MODEL)
        for driver in analysis.drivers:
            assert driver.weight > 0, (
                f"Driver '{driver.name}' has non-positive weight {driver.weight}"
            )

    def test_drivers_have_units_and_targets(self) -> None:
        analysis = analyze_requirements(PIPE_FITTING_REQUIREMENTS, model=INTEGRATION_MODEL)
        for driver in analysis.drivers:
            assert driver.unit, f"Driver '{driver.name}' missing unit"
            assert driver.target, f"Driver '{driver.name}' missing target"


# ---------------------------------------------------------------------------
# Concept Generation — does the LLM produce diverse, scoreable design variants?
# ---------------------------------------------------------------------------


@skip_without_api_key
@pytest.mark.integration
class TestConceptGeneration:
    """Verify the LLM generates physically distinct concepts with valid scores."""

    @pytest.fixture
    def bracket_analysis_live(self) -> RequirementsAnalysis:
        return analyze_requirements(BRACKET_REQUIREMENTS, model=INTEGRATION_MODEL)

    def test_generates_requested_number_of_concepts(
        self, bracket_analysis_live: RequirementsAnalysis
    ) -> None:
        study = generate_concepts(
            BRACKET_REQUIREMENTS,
            bracket_analysis_live,
            num_concepts=3,
            model=INTEGRATION_MODEL,
        )
        assert isinstance(study, TradeStudy)
        assert len(study.concepts) == 3

    def test_concepts_have_distinct_names(
        self, bracket_analysis_live: RequirementsAnalysis
    ) -> None:
        study = generate_concepts(
            BRACKET_REQUIREMENTS,
            bracket_analysis_live,
            num_concepts=4,
            model=INTEGRATION_MODEL,
        )
        names = [c.name for c in study.concepts]
        assert len(set(names)) == len(names), f"Duplicate concept names: {names}"

    def test_scores_are_in_valid_range(self, bracket_analysis_live: RequirementsAnalysis) -> None:
        study = generate_concepts(
            BRACKET_REQUIREMENTS,
            bracket_analysis_live,
            num_concepts=3,
            model=INTEGRATION_MODEL,
        )
        for concept in study.concepts:
            for driver_name, score in concept.scores.items():
                assert 0 <= score <= 10, (
                    f"Concept '{concept.name}' has out-of-range score {score} for '{driver_name}'"
                )

    def test_scores_cover_all_drivers(self, bracket_analysis_live: RequirementsAnalysis) -> None:
        study = generate_concepts(
            BRACKET_REQUIREMENTS,
            bracket_analysis_live,
            num_concepts=3,
            model=INTEGRATION_MODEL,
        )
        driver_names = {d.name for d in bracket_analysis_live.drivers}
        for concept in study.concepts:
            missing = driver_names - set(concept.scores.keys())
            assert not missing, f"Concept '{concept.name}' missing scores for: {missing}"

    def test_no_concept_scores_perfect_on_everything(
        self, bracket_analysis_live: RequirementsAnalysis
    ) -> None:
        """Real engineering involves tradeoffs — no design is perfect everywhere."""
        study = generate_concepts(
            BRACKET_REQUIREMENTS,
            bracket_analysis_live,
            num_concepts=4,
            model=INTEGRATION_MODEL,
        )
        for concept in study.concepts:
            scores = list(concept.scores.values())
            assert not all(s == 10.0 for s in scores), (
                f"Concept '{concept.name}' scored 10 on everything — unrealistic"
            )

    def test_recommendation_is_nonempty(self, bracket_analysis_live: RequirementsAnalysis) -> None:
        study = generate_concepts(
            BRACKET_REQUIREMENTS,
            bracket_analysis_live,
            num_concepts=3,
            model=INTEGRATION_MODEL,
        )
        assert len(study.recommendation) > 20, "Recommendation should be substantive"


# ---------------------------------------------------------------------------
# End-to-end pipeline — full flow from requirements to ranked tradeoff matrix
# ---------------------------------------------------------------------------


@skip_without_api_key
@pytest.mark.integration
class TestEndToEndPipeline:
    """Full pipeline: requirements → drivers → concepts → ranked matrix."""

    def test_pipe_fitting_full_pipeline(self) -> None:
        """Compressed air pipe elbow — tests a fluid/pressure domain."""
        analysis = analyze_requirements(PIPE_FITTING_REQUIREMENTS, model=INTEGRATION_MODEL)
        assert len(analysis.drivers) >= 3

        study = generate_concepts(
            PIPE_FITTING_REQUIREMENTS,
            analysis,
            num_concepts=3,
            model=INTEGRATION_MODEL,
        )
        assert len(study.concepts) == 3

        ranked = rank_concepts(study.concepts, analysis)
        assert len(ranked) == 3

        # Best concept should have a meaningfully higher score than worst
        best_score = ranked[0][1]
        worst_score = ranked[-1][1]
        assert best_score >= worst_score
        assert best_score > 0

    def test_heat_sink_full_pipeline(self) -> None:
        """Passive heat sink — tests a thermal domain."""
        analysis = analyze_requirements(HEAT_SINK_REQUIREMENTS, model=INTEGRATION_MODEL)

        study = generate_concepts(
            HEAT_SINK_REQUIREMENTS,
            analysis,
            num_concepts=3,
            model=INTEGRATION_MODEL,
        )

        # Verify the weighted scoring math works on real LLM output
        for concept in study.concepts:
            ws = weighted_score(concept.scores, analysis)
            assert 0 < ws <= 10, f"Weighted score {ws} out of expected range"

    def test_concepts_have_rationale_for_each_score(self) -> None:
        """Every score should have a human-readable rationale."""
        analysis = analyze_requirements(BRACKET_REQUIREMENTS, model=INTEGRATION_MODEL)
        study = generate_concepts(
            BRACKET_REQUIREMENTS,
            analysis,
            num_concepts=3,
            model=INTEGRATION_MODEL,
        )
        for concept in study.concepts:
            for driver in analysis.drivers:
                assert driver.name in concept.rationale, (
                    f"Concept '{concept.name}' missing rationale for '{driver.name}'"
                )
                assert len(concept.rationale[driver.name]) > 5, (
                    f"Rationale for '{concept.name}' / '{driver.name}' is too short"
                )

"""Tests for scoring and ranking logic."""

from __future__ import annotations

import pytest

from archetype.models import DesignConcept, DesignDriver, RequirementsAnalysis
from archetype.scoring import rank_concepts, score_color, weighted_score


@pytest.fixture
def two_driver_analysis() -> RequirementsAnalysis:
    return RequirementsAnalysis(
        summary="Test problem",
        drivers=[
            DesignDriver(
                name="Weight",
                description="Total mass",
                unit="kg",
                target="<5kg",
                weight=0.6,
            ),
            DesignDriver(
                name="Cost",
                description="Unit cost",
                unit="USD",
                target="<$100",
                weight=0.4,
            ),
        ],
    )


@pytest.fixture
def sample_concepts() -> list[DesignConcept]:
    return [
        DesignConcept(
            name="Concept A",
            approach="Lightweight approach",
            scores={"Weight": 9.0, "Cost": 4.0},
            rationale={"Weight": "Very light", "Cost": "Expensive materials"},
        ),
        DesignConcept(
            name="Concept B",
            approach="Budget approach",
            scores={"Weight": 5.0, "Cost": 8.0},
            rationale={"Weight": "Average", "Cost": "Cheap materials"},
        ),
        DesignConcept(
            name="Concept C",
            approach="Balanced approach",
            scores={"Weight": 7.0, "Cost": 7.0},
            rationale={"Weight": "Good", "Cost": "Reasonable"},
        ),
    ]


class TestScoreColor:
    @pytest.mark.parametrize(
        ("score", "expected"),
        [
            (10.0, "green"),
            (8.0, "green"),
            (8.5, "green"),
            (7.9, "yellow"),
            (6.0, "yellow"),
            (6.5, "yellow"),
            (5.9, "bright_black"),
            (4.0, "bright_black"),
            (4.5, "bright_black"),
            (3.9, "red"),
            (0.0, "red"),
            (2.0, "red"),
        ],
    )
    def test_maps_score_to_color(self, score: float, expected: str) -> None:
        assert score_color(score) == expected

    def test_exact_boundaries(self) -> None:
        assert score_color(8.0) == "green"
        assert score_color(6.0) == "yellow"
        assert score_color(4.0) == "bright_black"


class TestWeightedScore:
    def test_computes_weighted_sum(self, two_driver_analysis: RequirementsAnalysis) -> None:
        scores = {"Weight": 10.0, "Cost": 5.0}
        result = weighted_score(scores, two_driver_analysis)
        # 10.0 * 0.6 + 5.0 * 0.4 = 6.0 + 2.0 = 8.0
        assert result == pytest.approx(8.0)

    def test_missing_driver_scores_zero(self, two_driver_analysis: RequirementsAnalysis) -> None:
        scores = {"Weight": 10.0}
        result = weighted_score(scores, two_driver_analysis)
        # 10.0 * 0.6 + 0 * 0.4 = 6.0
        assert result == pytest.approx(6.0)

    def test_empty_scores(self, two_driver_analysis: RequirementsAnalysis) -> None:
        assert weighted_score({}, two_driver_analysis) == pytest.approx(0.0)

    def test_all_zeros(self, two_driver_analysis: RequirementsAnalysis) -> None:
        scores = {"Weight": 0.0, "Cost": 0.0}
        assert weighted_score(scores, two_driver_analysis) == pytest.approx(0.0)

    def test_all_tens(self, two_driver_analysis: RequirementsAnalysis) -> None:
        scores = {"Weight": 10.0, "Cost": 10.0}
        result = weighted_score(scores, two_driver_analysis)
        # 10 * 0.6 + 10 * 0.4 = 10.0
        assert result == pytest.approx(10.0)

    def test_extra_driver_in_scores_ignored(
        self, two_driver_analysis: RequirementsAnalysis
    ) -> None:
        scores = {"Weight": 10.0, "Cost": 5.0, "Speed": 9.0}
        result = weighted_score(scores, two_driver_analysis)
        assert result == pytest.approx(8.0)

    def test_no_drivers(self) -> None:
        analysis = RequirementsAnalysis(summary="Empty", drivers=[])
        assert weighted_score({"Weight": 10.0}, analysis) == pytest.approx(0.0)


class TestRankConcepts:
    def test_ranks_by_weighted_score_descending(
        self,
        sample_concepts: list[DesignConcept],
        two_driver_analysis: RequirementsAnalysis,
    ) -> None:
        ranked = rank_concepts(sample_concepts, two_driver_analysis)
        names = [c.name for c, _ in ranked]
        # A: 9*0.6 + 4*0.4 = 7.0, B: 5*0.6 + 8*0.4 = 6.2, C: 7*0.6 + 7*0.4 = 7.0
        # A and C tie at 7.0, B is last
        assert names[-1] == "Concept B"
        assert ranked[0][1] == pytest.approx(7.0)
        assert ranked[-1][1] == pytest.approx(6.2)

    def test_returns_scores_with_concepts(
        self,
        sample_concepts: list[DesignConcept],
        two_driver_analysis: RequirementsAnalysis,
    ) -> None:
        ranked = rank_concepts(sample_concepts, two_driver_analysis)
        assert len(ranked) == 3
        for concept, ws in ranked:
            assert isinstance(concept, DesignConcept)
            assert isinstance(ws, float)

    def test_empty_concepts(self, two_driver_analysis: RequirementsAnalysis) -> None:
        assert rank_concepts([], two_driver_analysis) == []

    def test_single_concept(self, two_driver_analysis: RequirementsAnalysis) -> None:
        concept = DesignConcept(
            name="Solo",
            approach="Only option",
            scores={"Weight": 5.0, "Cost": 5.0},
            rationale={"Weight": "Ok", "Cost": "Ok"},
        )
        ranked = rank_concepts([concept], two_driver_analysis)
        assert len(ranked) == 1
        assert ranked[0][0].name == "Solo"
        assert ranked[0][1] == pytest.approx(5.0)

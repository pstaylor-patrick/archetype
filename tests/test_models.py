"""Tests for Pydantic model validation — ensuring the schema enforces engineering constraints."""

from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from archetype.models import DesignConcept, DesignDriver, RequirementsAnalysis, TradeStudy


class TestDesignDriver:
    def test_valid_driver(self) -> None:
        d = DesignDriver(
            name="Weight", description="Total mass", unit="kg", target="<5kg", weight=0.3
        )
        assert d.name == "Weight"
        assert d.weight == 0.3

    def test_weight_must_be_in_range(self) -> None:
        with pytest.raises(ValidationError, match="greater than or equal to 0"):
            DesignDriver(name="X", description="X", unit="X", target="X", weight=-0.1)
        with pytest.raises(ValidationError, match="less than or equal to 1"):
            DesignDriver(name="X", description="X", unit="X", target="X", weight=1.1)

    def test_boundary_weights(self) -> None:
        d0 = DesignDriver(name="X", description="X", unit="X", target="X", weight=0.0)
        d1 = DesignDriver(name="X", description="X", unit="X", target="X", weight=1.0)
        assert d0.weight == 0.0
        assert d1.weight == 1.0


class TestRequirementsAnalysis:
    def test_roundtrip_json(self) -> None:
        """Models must survive JSON serialization — this is how we parse LLM output."""
        analysis = RequirementsAnalysis(
            summary="Test bracket",
            drivers=[
                DesignDriver(
                    name="Weight", description="Mass", unit="kg", target="<2kg", weight=0.5
                ),
                DesignDriver(
                    name="Cost", description="Price", unit="USD", target="<$10", weight=0.5
                ),
            ],
        )
        json_str = analysis.model_dump_json()
        restored = RequirementsAnalysis.model_validate_json(json_str)
        assert restored.summary == analysis.summary
        assert len(restored.drivers) == 2
        assert restored.drivers[0].weight == 0.5

    def test_schema_is_valid_json_schema(self) -> None:
        """The schema we send to the LLM must be valid JSON."""
        schema = RequirementsAnalysis.model_json_schema()
        json_str = json.dumps(schema)
        parsed = json.loads(json_str)
        assert "properties" in parsed

    def test_empty_drivers_allowed(self) -> None:
        a = RequirementsAnalysis(summary="Empty problem", drivers=[])
        assert a.drivers == []


class TestDesignConcept:
    def test_scores_and_rationale_are_dicts(self) -> None:
        c = DesignConcept(
            name="A",
            approach="Simple",
            scores={"Weight": 8.0, "Cost": 6.0},
            rationale={"Weight": "Light", "Cost": "Moderate"},
        )
        assert c.scores["Weight"] == 8.0
        assert "Light" in c.rationale["Weight"]


class TestTradeStudy:
    def test_roundtrip_json(self) -> None:
        study = TradeStudy(
            concepts=[
                DesignConcept(
                    name="A",
                    approach="First",
                    scores={"W": 7.0},
                    rationale={"W": "ok"},
                ),
            ],
            recommendation="Go with A",
        )
        json_str = study.model_dump_json()
        restored = TradeStudy.model_validate_json(json_str)
        assert len(restored.concepts) == 1
        assert restored.recommendation == "Go with A"

    def test_multiple_concepts_preserve_order(self) -> None:
        concepts = [
            DesignConcept(
                name=f"C{i}", approach=f"Approach {i}", scores={"X": float(i)}, rationale={"X": "r"}
            )
            for i in range(5)
        ]
        study = TradeStudy(concepts=concepts, recommendation="Pick C4")
        assert [c.name for c in study.concepts] == ["C0", "C1", "C2", "C3", "C4"]

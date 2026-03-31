"""Shared fixtures and markers for archetype tests."""

from __future__ import annotations

import os

import pytest

from archetype.models import DesignConcept, DesignDriver, RequirementsAnalysis, TradeStudy


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "integration: requires ANTHROPIC_API_KEY and makes real API calls")


def has_api_key() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


skip_without_api_key = pytest.mark.skipif(
    not has_api_key(),
    reason="ANTHROPIC_API_KEY not set",
)


# ---------------------------------------------------------------------------
# Budget-friendly model: use haiku for integration tests to minimize cost
# ---------------------------------------------------------------------------
INTEGRATION_MODEL = "claude-haiku-4-5-20251001"


# ---------------------------------------------------------------------------
# Compact engineering requirement fixtures (short = fewer input tokens)
# ---------------------------------------------------------------------------

BRACKET_REQUIREMENTS = """\
Design a wall-mount bracket for a 5kg security camera.
- Must survive 2G vibration
- Outdoor use, -20°C to +50°C
- Budget: under $12/unit at 1000/year volume
- Maximum deflection: 1mm under load
- Material must resist corrosion (rain exposure)
"""

HEAT_SINK_REQUIREMENTS = """\
Design a passive heat sink for a 25W embedded processor.
- Maximum junction temperature: 85°C at 40°C ambient
- Envelope: 60mm x 60mm x 30mm max
- Must mount with 4x M3 screws on 45mm square pattern
- Target weight: under 150g
- Production volume: 5000/year, target cost under $4/unit
"""

PIPE_FITTING_REQUIREMENTS = """\
Design a 90-degree pipe elbow for a compressed air system.
- Line pressure: 10 bar continuous, 15 bar peak
- Pipe OD: 25mm
- Flow rate: 200 L/min
- Minimize pressure drop
- Operating temperature: 5°C to 60°C
- Must pass 100,000 pressure cycles without fatigue failure
- Budget: under $6/unit at 2000/year
"""


# ---------------------------------------------------------------------------
# Pre-built model fixtures for unit-level tests
# ---------------------------------------------------------------------------

@pytest.fixture
def bracket_analysis() -> RequirementsAnalysis:
    """A realistic bracket requirements analysis for testing downstream logic."""
    return RequirementsAnalysis(
        summary="Wall-mount bracket for a 5kg security camera in outdoor conditions",
        drivers=[
            DesignDriver(
                name="Structural Integrity",
                description="Withstand 5kg static + 2G vibration loads with <1mm deflection",
                unit="mm",
                target="<1mm deflection",
                weight=0.30,
            ),
            DesignDriver(
                name="Corrosion Resistance",
                description="Survive outdoor rain exposure without degradation",
                unit="years",
                target=">10 years",
                weight=0.20,
            ),
            DesignDriver(
                name="Cost",
                description="Unit manufacturing cost at 1000/year volume",
                unit="USD",
                target="<$12",
                weight=0.25,
            ),
            DesignDriver(
                name="Thermal Range",
                description="Maintain properties across operating temperature range",
                unit="°C",
                target="-20 to +50°C",
                weight=0.10,
            ),
            DesignDriver(
                name="Manufacturability",
                description="Ease of manufacture at specified volume",
                unit="qualitative",
                target="Standard processes at 1000/year",
                weight=0.15,
            ),
        ],
    )


@pytest.fixture
def bracket_concepts(bracket_analysis: RequirementsAnalysis) -> list[DesignConcept]:
    """Realistic bracket concepts matching the bracket_analysis drivers."""
    driver_names = [d.name for d in bracket_analysis.drivers]
    return [
        DesignConcept(
            name="304SS Sheet Metal",
            approach="Bent stainless steel sheet with welded gussets",
            scores=dict(zip(driver_names, [8.0, 9.0, 6.0, 9.0, 7.0])),
            rationale=dict(zip(driver_names, [
                "Strong but heavier than needed",
                "Excellent corrosion resistance",
                "Material cost moderate, welding adds labor",
                "Full range no issue",
                "Standard sheet metal fab",
            ])),
        ),
        DesignConcept(
            name="Die-Cast Aluminum",
            approach="A380 aluminum die casting with powder coat finish",
            scores=dict(zip(driver_names, [7.0, 7.0, 8.0, 8.0, 9.0])),
            rationale=dict(zip(driver_names, [
                "Adequate but lower stiffness than steel",
                "Good with powder coat, bare aluminum would pit",
                "Low unit cost at volume from die casting",
                "Aluminum handles range well",
                "High-volume die casting is very repeatable",
            ])),
        ),
        DesignConcept(
            name="Glass-Filled Nylon",
            approach="Injection molded PA66-GF30 with brass inserts",
            scores=dict(zip(driver_names, [6.0, 8.0, 9.0, 6.0, 9.0])),
            rationale=dict(zip(driver_names, [
                "Adequate for static but flex under vibration",
                "Inherently corrosion-proof",
                "Very low unit cost at volume",
                "Nylon loses strength above 40°C under load",
                "Injection molding is ideal at 1000/year",
            ])),
        ),
    ]


@pytest.fixture
def bracket_study(bracket_concepts: list[DesignConcept]) -> TradeStudy:
    return TradeStudy(
        concepts=bracket_concepts,
        recommendation=(
            "Die-cast aluminum offers the best balance of cost, manufacturability, "
            "and adequate structural performance with proper powder coat finish."
        ),
    )

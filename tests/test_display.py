"""Tests for Rich terminal display output."""

from __future__ import annotations

from io import StringIO
from typing import List

from rich.console import Console

from archetype.display import print_analysis, print_tradeoff_matrix
from archetype.models import DesignConcept, RequirementsAnalysis, TradeStudy


def _capture(
    fn: object,
    *args: object,
) -> str:
    """Capture Rich console output as plain text."""
    buf = StringIO()
    console = Console(file=buf, force_terminal=True, width=120)
    fn(*args, console)  # type: ignore[operator]
    return buf.getvalue()


class TestPrintAnalysis:
    def test_renders_summary_panel(self, bracket_analysis: RequirementsAnalysis) -> None:
        output = _capture(print_analysis, bracket_analysis)
        assert "Problem Summary" in output
        assert "Wall-mount bracket" in output

    def test_renders_all_drivers(self, bracket_analysis: RequirementsAnalysis) -> None:
        output = _capture(print_analysis, bracket_analysis)
        for driver in bracket_analysis.drivers:
            assert driver.name in output

    def test_renders_weight_percentages(self, bracket_analysis: RequirementsAnalysis) -> None:
        output = _capture(print_analysis, bracket_analysis)
        assert "30%" in output
        assert "25%" in output

    def test_handles_empty_drivers(self) -> None:
        analysis = RequirementsAnalysis(summary="Nothing here", drivers=[])
        output = _capture(print_analysis, analysis)
        assert "Nothing here" in output


class TestPrintTradeoffMatrix:
    def test_renders_all_concept_names(
        self,
        bracket_study: TradeStudy,
        bracket_analysis: RequirementsAnalysis,
    ) -> None:
        output = _capture(print_tradeoff_matrix, bracket_study, bracket_analysis)
        for concept in bracket_study.concepts:
            assert concept.name in output

    def test_renders_recommendation(
        self,
        bracket_study: TradeStudy,
        bracket_analysis: RequirementsAnalysis,
    ) -> None:
        output = _capture(print_tradeoff_matrix, bracket_study, bracket_analysis)
        assert "Recommendation" in output
        assert "Die-cast aluminum" in output

    def test_renders_weighted_totals(
        self,
        bracket_study: TradeStudy,
        bracket_analysis: RequirementsAnalysis,
    ) -> None:
        output = _capture(print_tradeoff_matrix, bracket_study, bracket_analysis)
        assert "Weighted" in output

    def test_renders_driver_column_headers(
        self,
        bracket_study: TradeStudy,
        bracket_analysis: RequirementsAnalysis,
    ) -> None:
        output = _capture(print_tradeoff_matrix, bracket_study, bracket_analysis)
        for driver in bracket_analysis.drivers:
            # Rich may truncate long names with ellipsis; check a prefix is present
            prefix = driver.name[:8]
            assert prefix in output, f"Expected prefix '{prefix}' from '{driver.name}' in output"

"""Rich terminal display for tradeoff matrices."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from archetype.models import RequirementsAnalysis, TradeStudy


def _score_color(score: float) -> str:
    """Map a 0-10 score to a color."""
    if score >= 8:
        return "green"
    if score >= 6:
        return "yellow"
    if score >= 4:
        return "bright_black"
    return "red"


def _weighted_score(concept_scores: dict[str, float], analysis: RequirementsAnalysis) -> float:
    """Calculate the weighted composite score for a concept."""
    total = 0.0
    for driver in analysis.drivers:
        total += concept_scores.get(driver.name, 0) * driver.weight
    return total


def print_analysis(analysis: RequirementsAnalysis, console: Console) -> None:
    """Print the requirements decomposition."""
    console.print()
    console.print(Panel(analysis.summary, title="Problem Summary", border_style="blue"))

    table = Table(title="Design Drivers", show_lines=True)
    table.add_column("Driver", style="bold cyan", min_width=12)
    table.add_column("Description", min_width=20)
    table.add_column("Target", style="green", min_width=10)
    table.add_column("Weight", justify="right", style="yellow", min_width=8)

    for driver in analysis.drivers:
        weight_bar = "█" * int(driver.weight * 20) + "░" * (20 - int(driver.weight * 20))
        table.add_row(
            driver.name,
            driver.description,
            f"{driver.target} ({driver.unit})",
            f"{driver.weight:.0%} {weight_bar}",
        )

    console.print(table)


def print_tradeoff_matrix(
    study: TradeStudy, analysis: RequirementsAnalysis, console: Console
) -> None:
    """Print the scored tradeoff matrix with weighted totals."""
    table = Table(title="Tradeoff Matrix", show_lines=True, padding=(0, 1))

    table.add_column("Concept", style="bold", min_width=14)
    for driver in analysis.drivers:
        table.add_column(
            f"{driver.name}\n({driver.weight:.0%})",
            justify="center",
            min_width=10,
        )
    table.add_column("Weighted\nTotal", justify="center", style="bold", min_width=10)

    scored_concepts = []
    for concept in study.concepts:
        ws = _weighted_score(concept.scores, analysis)
        scored_concepts.append((concept, ws))

    scored_concepts.sort(key=lambda x: x[1], reverse=True)
    best_score = scored_concepts[0][1] if scored_concepts else 0

    for concept, ws in scored_concepts:
        row = [concept.name]
        for driver in analysis.drivers:
            score = concept.scores.get(driver.name, 0)
            color = _score_color(score)
            row.append(f"[{color}]{score:.1f}[/{color}]")

        total_color = "bold green" if ws == best_score else "white"
        row.append(f"[{total_color}]{ws:.2f}[/{total_color}]")
        table.add_row(*row)

    console.print()
    console.print(table)

    console.print()
    for concept in study.concepts:
        concept_text = Text()
        concept_text.append(f"  {concept.name}: ", style="bold")
        concept_text.append(concept.approach)
        console.print(concept_text)
    console.print()

    console.print(
        Panel(study.recommendation, title="Recommendation", border_style="green")
    )

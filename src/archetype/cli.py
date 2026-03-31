"""Archetype CLI — engineering requirements to tradeoff matrices."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from archetype import __version__
from archetype.display import print_analysis, print_tradeoff_matrix
from archetype.engine import analyze_requirements, generate_concepts

app = typer.Typer(
    name="archetype",
    help="Decompose engineering requirements into design concepts and weighted tradeoff matrices.",
    no_args_is_help=True,
)
console = Console()


def version_callback(value: bool) -> None:
    if value:
        console.print(f"archetype {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        help="Show version and exit.",
        callback=version_callback,
        is_eager=True,
    ),
) -> None:
    """Archetype — engineering requirements to tradeoff matrices."""


@app.command()
def analyze(
    source: Optional[Path] = typer.Argument(
        None,
        help="Path to a requirements file. Reads from stdin if omitted.",
        exists=True,
        readable=True,
    ),
    concepts: int = typer.Option(
        4,
        "--concepts",
        "-n",
        help="Number of design concepts to generate.",
        min=2,
        max=8,
    ),
    model: str = typer.Option(
        "claude-sonnet-4-20250514",
        "--model",
        "-m",
        help="Anthropic model to use.",
    ),
    drivers_only: bool = typer.Option(
        False,
        "--drivers-only",
        help="Only extract design drivers, skip concept generation.",
    ),
    api_key: Optional[str] = typer.Option(
        None,
        "--api-key",
        envvar="ANTHROPIC_API_KEY",
        help="Anthropic API key. Falls back to ANTHROPIC_API_KEY env var.",
    ),
) -> None:
    """Analyze engineering requirements and generate a design tradeoff matrix.

    Reads requirements from a file or stdin, decomposes them into weighted
    design drivers, generates design concept variants, and scores each concept
    in a tradeoff matrix.

    Examples:

        archetype analyze requirements.txt

        echo "Design a heat sink for a 50W LED array" | archetype analyze

        archetype analyze specs.txt --concepts 6 --drivers-only
    """
    if source:
        requirements = source.read_text()
    elif not sys.stdin.isatty():
        requirements = sys.stdin.read()
    else:
        console.print("[red]Error:[/red] Provide a requirements file or pipe text to stdin.")
        console.print("  archetype analyze requirements.txt")
        console.print('  echo "Design a bracket..." | archetype analyze')
        raise typer.Exit(code=1)

    requirements = requirements.strip()
    if not requirements:
        console.print("[red]Error:[/red] Empty requirements.")
        raise typer.Exit(code=1)

    with console.status("[bold blue]Extracting design drivers..."):
        analysis = analyze_requirements(requirements, api_key=api_key, model=model)

    print_analysis(analysis, console)

    if drivers_only:
        raise typer.Exit()

    with console.status("[bold blue]Generating design concepts..."):
        study = generate_concepts(
            requirements, analysis, num_concepts=concepts, api_key=api_key, model=model
        )

    print_tradeoff_matrix(study, analysis, console)

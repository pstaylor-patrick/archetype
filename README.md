# archetype

Decompose engineering requirements into design concepts and weighted tradeoff matrices.

Feed it a natural language engineering spec — a mounting bracket, a heat exchanger, an enclosure — and archetype uses an LLM to do what a junior design engineer does:

1. **Extract design drivers** from the requirements (weight, cost, thermal performance, manufacturability, etc.) with relative importance weights
2. **Generate diverse design concepts** — different materials, geometries, manufacturing methods
3. **Score each concept** against every driver on a 0-10 scale with rationale
4. **Rank by weighted composite score** and recommend the best option

The output is a tradeoff matrix — the standard tool of systems engineering trade studies.

## Install

```bash
pip install -e .
```

## Usage

```bash
# Analyze a requirements file
archetype analyze examples/bracket.txt

# Pipe requirements from stdin
echo "Design a heat sink for a 50W LED array, max 200g, under $15" | archetype analyze

# Generate more concepts
archetype analyze examples/heat-exchanger.txt --concepts 6

# Only extract design drivers (skip concept generation)
archetype analyze examples/enclosure.txt --drivers-only
```

## Example

```bash
$ archetype analyze examples/bracket.txt
```

```
╭──────────────── Problem Summary ─────────────────╮
│ Design a mounting bracket for a 15kg satellite    │
│ communication antenna in a marine environment     │
│ with vibration, thermal, and corrosion            │
│ requirements.                                     │
╰──────────────────────────────────────────────────╯

         Design Drivers
┌──────────────┬────────────┬──────────┬─────────┐
│ Driver       │ Target     │ Unit     │ Weight  │
├──────────────┼────────────┼──────────┼─────────┤
│ Structural   │ 3G, 0.5mm  │ mm       │ 25%     │
│ Weight       │ <800g      │ grams    │ 15%     │
│ Cost         │ <$45/unit  │ USD      │ 20%     │
│ Corrosion    │ 15yr marine│ years    │ 15%     │
│ Thermal      │ -40 to 85°C│ °C       │ 10%     │
│ Mfg Ease     │ 500/yr vol │ units/yr │ 15%     │
└──────────────┴────────────┴──────────┴─────────┘

             Tradeoff Matrix
┌──────────────┬─────┬─────┬─────┬─────┬─────┬─────┬───────┐
│ Concept      │Struc│ Wt  │Cost │Corr │Therm│ Mfg │ Total │
├──────────────┼─────┼─────┼─────┼─────┼─────┼─────┼───────┤
│ 316SS Sheet  │ 8.0 │ 5.0 │ 7.0 │ 9.0 │ 8.0 │ 8.0 │  7.35 │
│ Ti-6Al-4V CNC│ 9.5 │ 7.0 │ 4.0 │ 9.5 │ 9.0 │ 5.0 │  7.18 │
│ Al 5083 Cast │ 7.0 │ 8.0 │ 8.0 │ 6.0 │ 7.0 │ 7.0 │  7.10 │
│ GFRP Molded  │ 7.5 │ 9.0 │ 6.0 │ 9.0 │ 6.0 │ 6.0 │  7.08 │
└──────────────┴─────┴─────┴─────┴─────┴─────┴─────┴───────┘

╭──────────────── Recommendation ──────────────────╮
│ 316 Stainless Steel sheet metal bracket offers    │
│ the best balance of structural performance,       │
│ corrosion resistance, and manufacturing           │
│ simplicity at the target cost point.              │
╰──────────────────────────────────────────────────╯
```

*(Actual output will vary based on LLM response)*

## How It Works

1. **Requirements analysis** — sends the raw spec to Claude, which returns structured JSON matching a Pydantic schema: design drivers with names, descriptions, units, targets, and importance weights
2. **Concept generation** — sends the requirements + extracted drivers back to Claude, asking for N diverse design concepts each scored 0-10 against every driver with rationale
3. **Display** — renders a Rich terminal table with color-coded scores, weighted composite totals, concept descriptions, and a recommendation

## Configuration

Set your Anthropic API key:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

Or pass it directly:

```bash
archetype analyze examples/bracket.txt --api-key sk-ant-...
```

## Options

| Flag | Default | Description |
|------|---------|-------------|
| `--concepts`, `-n` | 4 | Number of design concepts (2-8) |
| `--model`, `-m` | `claude-sonnet-4-20250514` | Anthropic model |
| `--drivers-only` | false | Only extract drivers, skip concepts |
| `--api-key` | `$ANTHROPIC_API_KEY` | Anthropic API key |
| `--version`, `-v` | — | Show version |

## Examples

Three example requirement specs are included:

- [`examples/bracket.txt`](examples/bracket.txt) — satellite antenna mounting bracket (vibration, marine, thermal)
- [`examples/heat-exchanger.txt`](examples/heat-exchanger.txt) — 500W laser cooling (thermal, pressure drop, fatigue)
- [`examples/enclosure.txt`](examples/enclosure.txt) — outdoor IoT sensor enclosure (IP67, drop test, UV)

## Why

This is a miniature version of what an engineering AGI does: distill requirements into design drivers, generate concept variants, run first-order trades, and recommend a direction. The real version uses physics simulations and CAD — this one uses an LLM to approximate the reasoning step.

## License

MIT

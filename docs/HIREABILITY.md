# Hireability and discoverability index

Lean entry point for hiring readers and repository classification. This page
indexes inspectable surfaces; it does not assert `READY`, benchmark scores, win
rates, rankings, or hiring outcomes. A tip-cite records provenance only.

## Purpose

Deterministic strategy bots and local match infrastructure for the 2011
[Ants AI Challenge](https://ants.aichallenge.org/): game engine, protocol and
sandbox, several bot implementations, fixed opponents, seeded benchmark runners,
and a browser replay viewer. Evidence is meant to be checked locally against
retained result packets, not inferred from documentation prose.

## Stack

| Layer | Technology |
| --- | --- |
| Language | Python 3.12+ ([`pyproject.toml`](../pyproject.toml)) |
| Dependencies | [uv](https://docs.astral.sh/uv/) (`uv sync --all-extras`) |
| Automation | [`Makefile`](../Makefile) targets for test, validate, benchmarks, visualization |
| Containers | Docker image and VS Code dev container (see README Quick start) |
| Viewer | [`visualizer/`](../visualizer/) local replay UI |

## Run and demo (minimal path)

```bash
git clone https://github.com/T-Py-T/ants-strategy-agent.git
cd ants-strategy-agent
uv sync --all-extras
make pytest
make test
make visualize-evidence
```

`make test` runs a short game through the local engine. `make visualize-evidence`
opens the retained replay referenced from
[`results/current-evidence-v1/`](../results/current-evidence-v1/). Full command
lists and matchup targets live in [`README.md`](../README.md).

## Licensing

- Project grant and SPDX identifier: [`LICENSE`](../LICENSE) (Apache-2.0 for
  Taylor's code and challenge infrastructure).
- Component boundaries and retained historical sources:
  [`docs/LICENSING.md`](LICENSING.md), [`THIRD_PARTY_NOTICES.md`](../THIRD_PARTY_NOTICES.md).
- The SPDX line and trailing provenance appendix in `LICENSE` are not part of
  the license grant.

## Suggested GitHub topics

Set these in the repository **Topics** field (wiki and search discoverability
only; not a readiness signal):

`python` `game-ai` `ants-aichallenge` `strategy-bots` `benchmarking`
`replay-visualizer` `reproducible-research` `simulation` `apache-2.0`

## Hiring-review pointers

| Signal | Where to start |
| --- | --- |
| Systems ownership | [`src/ants/`](../src/ants/), [`Makefile`](../Makefile) |
| Algorithm design | [`src/bots/`](../src/bots/), [`STRATEGY_LINEAGE.md`](STRATEGY_LINEAGE.md) |
| Reproducibility | [`results/current-evidence-v1/`](../results/current-evidence-v1/) |
| Limitations and held work | [`docs/OPEN_PROBLEMS.md`](OPEN_PROBLEMS.md), [`ROADMAP.md`](../ROADMAP.md) |
| Contributor bar | [`CONTRIBUTING.md`](../CONTRIBUTING.md) |

The detailed hiring-review table remains in [`README.md`](../README.md#hiring-review-path).

## Tip-cite bank

> Tip-cite bank: base main `00de3e4e`
> Tip-cite bank: Ship 230 — this PR pending Steward

These lines record provenance only. The Steward resolves the 8-character tip
against `main` when a full SHA or merge context is needed. A tip-cite does not
establish readiness or substitute for the retained evidence packet.

# Roadmap

This document is a **planning surface** for hireability and engineering follow-up.
It records intended scope, known gaps, and documentation hygiene — not acceptance,
readiness, benchmark scores, or hiring outcomes.

## Status boundary

- This roadmap makes **no `READY` claim**.
- Labels such as `GAP`, `UNTESTED`, and `BLOCKED-AUTH` describe planning state
  only. They do not close an item or certify evidence.
- Only results retained in a versioned evidence packet (for example
  [`results/current-evidence-v1/`](results/current-evidence-v1/)) may be cited as
  recorded outcomes. README prose and roadmap items are not substitutes.

## Baseline provenance

Planning is anchored to the current `main` tip at the time of this document:

```text
T-Py-T/ants-strategy-agent #97 fb524662
```

The Steward resolves the 8-character tip against `main` when a full SHA or merge
context is needed. A tip-cite records provenance; it does not establish readiness.

## What exists today (inspectable, not asserted)

The repository already provides a local path from code to evidence:

| Surface | Location | Planning note |
| --- | --- | --- |
| Match infrastructure | [`src/ants/`](src/ants/), [`Makefile`](Makefile) | Engine, protocol, sandbox, and repeatable commands are present and covered by tests. |
| Algorithmic policies | [`src/bots/`](src/bots/), [`docs/STRATEGY_LINEAGE.md`](docs/STRATEGY_LINEAGE.md) | `AdvancedBot` is the default; `InfluenceBot` and partial `XathisBot` are comparison baselines with stated lineage boundaries. |
| Retained evidence packet | [`results/current-evidence-v1/`](results/current-evidence-v1/) | One frozen `current-evidence-v1` workload exists; its scope and revision are bounded by [`benchmarks/current-evidence-v1.json`](benchmarks/current-evidence-v1.json). |
| Open inventory | [`docs/OPEN_PROBLEMS.md`](docs/OPEN_PROBLEMS.md) | Authoritative list of open and held work; this roadmap does not duplicate or relabel inventory closure criteria. |

The retained packet records commit `69bc75d6` and 14 draws under its declared
quick benchmark — not a universal strength claim. See
[`results/current-evidence-v1/README.md`](results/current-evidence-v1/README.md)
for the exact observed result.

## Planned work

Items below are derived from [`README.md`](README.md),
[`docs/OPEN_PROBLEMS.md`](docs/OPEN_PROBLEMS.md), and
[`docs/STRATEGY_LINEAGE.md`](docs/STRATEGY_LINEAGE.md). They are ordered for
review clarity, not priority commitment.

### Evidence and reproducibility

| Item | Label | Intent |
| --- | --- | --- |
| Refresh or extend `current-evidence-v1` when `main` materially changes bot, engine, or benchmark behavior | `GAP` | Keep the versioned packet, manifest, raw output, and replay aligned with the revision being reviewed. |
| Pre-declare comparison matrix (maps, opponents, seeds, turn cap) before presenting new matchup evidence | `GAP` | Reduce ad hoc benchmark scope; retain all raw outcomes and configuration. |
| Re-run retained workloads from a clean checkout and confirm manifest hashes before repeating a claim | `UNTESTED` | Standard reproduction check for any new or updated evidence packet. |

### Benchmark and policy comparison

| Item | Label | Intent |
| --- | --- | --- |
| Multi-seed, multi-map frozen comparison before any default-policy change (`AdvancedBot` vs `InfluenceBot`) | `UNTESTED` | [`docs/STRATEGY_LINEAGE.md`](docs/STRATEGY_LINEAGE.md) lists required metrics; single-match `make` targets are diagnostics only. |
| Broader executable comparison against preserved historical Xathis Java | `GAP` | Partial `XathisBot` is a regression opponent, not a validated faithful port of the leaderboard winner. |
| Statistical interpretation and exclusion notes for benchmark suites | `GAP` | Document uncertainty, coverage limits, and what the retained run does not establish. |

### Documentation and evidence-surface hygiene

| Item | Label | Intent |
| --- | --- | --- |
| Synchronize README, result packets, manifests, licensing notes, and strategy lineage when claims or scope change | `GAP` | Prevent drift between prose and retained artifacts (see open inventory). |
| Keep [`CHANGELOG.md`](CHANGELOG.md) tip-cite bank current after merged documentation ships | `GAP` | Compact provenance for hiring readers without inventing release or readiness status. |
| Maintain hiring-review path tables and pointers (`ROADMAP`, `OPEN_PROBLEMS`, `CONTRIBUTING`) as thin indexes | — | Planning docs point to evidence; they do not substitute for it. |

### Licensing and provenance

| Item | Label | Intent |
| --- | --- | --- |
| Component-level provenance review for historical Xathis-derived and influence-map-derived material | `BLOCKED-AUTH` | Where no license grant was found, terms remain a boundary rather than an assumption of project licensing ([`docs/LICENSING.md`](docs/LICENSING.md)). |
| Preserve upstream notices, source locations, and adaptation boundaries as code evolves | — | Required for honest attribution and third-party notice accuracy. |

### Reinforcement-learning track

| Item | Label | Intent |
| --- | --- | --- |
| Reproducible training configuration, checkpoints, and provenance record | `GAP` | Planned work per README and open inventory; no completed policy is asserted. |
| Frozen evaluation against maps, seeds, turn limits, and algorithmic opponents (including Xathis) | `GAP` | Use the same match and replay infrastructure; retain raw results and replays. |
| Separate RL artifacts from algorithmic baseline entry points | — | Keep inspectable deterministic baselines distinct from learned policies. |

## Working rule

Treat every result as scoped evidence. Reproduce using the same revision, map,
arguments, bot revisions, engine seed, player seed, and turn limit before
repeating a claim. If an input is missing, hold the claim — do not fill the gap
with an invented score, status, or `READY` label.

## Related documents

- Open and held inventory: [`docs/OPEN_PROBLEMS.md`](docs/OPEN_PROBLEMS.md)
- Contribution and validation expectations: [`CONTRIBUTING.md`](CONTRIBUTING.md)
- Strategy attribution and comparison bar: [`docs/STRATEGY_LINEAGE.md`](docs/STRATEGY_LINEAGE.md)
- Governance and tip-cite protocol: [`GOVERNANCE.md`](GOVERNANCE.md)

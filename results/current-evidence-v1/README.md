# Current-SHA deterministic evidence packet

This packet records the exact `current-evidence-v1` workload executed against
default-branch commit `69bc75d6e6bb26c5f68ca02432bf313aae4aa2b2`.

## Result

All 14 games completed without an engine error. Every game was a draw: zero
wins, zero losses, 14 draws. That is the complete observed result, not a claim
that the agent is generally strong or weak. The workload uses one master seed,
two games per matchup, a 200-turn cap, and fixed local opponents.

## Artifacts

- [`../../benchmarks/current-evidence-v1.json`](../../benchmarks/current-evidence-v1.json) freezes code, maps, opponents, hashes, seeds, rules, and limitations.
- [`benchmark-raw.json`](benchmark-raw.json) is the benchmark runner's unedited machine-readable output, including non-deterministic wall-clock durations.
- [`deterministic-result.json`](deterministic-result.json) removes only timing fields and is the byte-stable result projection used for reproduction checks.
- [`benchmark-summary.md`](benchmark-summary.md) is the runner's human-readable summary.
- [`replay/four-player-final.replay`](replay/four-player-final.replay) is the final four-player game's portable replay data.
- [`environment.json`](environment.json) records the local toolchain without hostname or absolute paths.
- [`manifest.json`](manifest.json) hashes every other retained artifact, including the frozen spec.

## Reproduce

From commit `69bc75d6e6bb26c5f68ca02432bf313aae4aa2b2`:

```bash
uv sync --all-extras
uv run python scripts/benchmark.py --quick --seed 42 \
  --log-dir /tmp/ants-current-evidence/logs \
  --output-dir /tmp/ants-current-evidence/summary
```

Compare matchups, seeds, turns, winners, outcomes, player ranks, scores, and
statuses to `deterministic-result.json`. Do not compare wall-clock durations.

The local visualizer can load the retained replay with:

```bash
python3 visualizer/visualize_locally.py \
  results/current-evidence-v1/replay/four-player-final.replay --nolaunch
```

The generated HTML is a disposable local rendering and is not retained in this
packet.

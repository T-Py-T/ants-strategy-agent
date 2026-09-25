# Open problems inventory

This is an inventory of open or deliberately held work for the ants strategy
agent. It is a planning and provenance surface, not an acceptance gate. An item
remaining in this document does not by itself make a build, match, or pull
request invalid; closure requires the evidence described for that item.

## Status boundary

- This inventory makes **no `READY` claim**.
- No benchmark score, win rate, ranking, hiring outcome, or other score is
  invented or implied here. Only results recorded in the versioned evidence
  packet should be cited.
- The reinforcement-learning track is **not READY**. It is planned work, not a
  completed training or evaluation result.

## Open and held items

| Item | Current state | What would close or materially reduce it |
| --- | --- | --- |
| Reproducible match evidence versus claims | The repository has runners, seeds, replays, and a retained evidence packet, but a claim is only as strong as the exact revision and inputs behind it. README prose must not be treated as a substitute for a recorded result. | Publish or point to the matching result packet with code revision, maps, arguments, bot revisions, engine/player seeds, turn limits, raw output, aggregates, and replay. Re-run it from a clean checkout and confirm the manifest. |
| Benchmark scope and comparison coverage | Existing matchups are useful engineering evidence, not a universal performance claim. Coverage, opponent selection, map variety, and statistical interpretation remain bounded by the retained run. | Define the comparison matrix in advance, retain all raw outcomes and configuration, repeat across declared seeds/maps, and document uncertainty and exclusions. |
| Licensing and provenance boundaries | Original Taylor code and Apache-licensed challenge infrastructure are separated from historical Xathis-derived and influence-map-derived material. Where no license grant was found, those terms remain a boundary rather than an assumption of project licensing. | Complete component-level provenance review, preserve upstream notices and source locations, and record a clear license grant or an explicit exclusion for every imported or adapted component. |
| Reinforcement-learning track | The planned RL work has trajectory, training, and frozen-evaluation requirements, but no completed policy is being asserted by this inventory. RL is not READY. | Add a reproducible training configuration and provenance record, then evaluate a named policy against frozen maps, seeds, turn limits, and algorithmic opponents—including Xathis—using retained results and replays. |
| Evidence-surface synchronization | README, result packets, manifests, replays, licensing notes, and strategy lineage can drift as the project evolves. | When a claim changes, update the relevant source, result packet, manifest, and documentation together; make the revision and scope explicit. |
| Historical strategy attribution | Strategy lineage and recovered/adapted code need to remain distinguishable from new implementation work. | Keep lineage notes, source references, adaptation boundaries, and applicable notices current as code changes. |

## Working rule

Treat every result as scoped evidence. Reproduce it using the same revision,
map, arguments, bot revisions, engine seed, player seed, and turn limit before
repeating a claim. If one of those inputs is missing, hold the claim rather
than filling the gap with an invented score or status.

## Tip-cite protocol

A tip-cite is a compact pointer for the Steward, not a readiness signal. In
banks and pull requests use exactly an 8-character hexadecimal tip together
with the PR number, for example:

```text
T-Py-T/ants-strategy-agent #<PR> <8-char-main-tip>
```

The Steward resolves the short tip against `main` when a full SHA or merge
context is needed. A blocked, incomplete, or untested item remains blocked or
incomplete; tip-cites never turn it into `READY`.

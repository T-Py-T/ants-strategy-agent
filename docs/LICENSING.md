# Licensing and provenance

This repository uses Apache-2.0 for Taylor's original contributions and for
the inherited AI Challenge infrastructure that upstream documentation identifies
as Apache-2.0. Two attributed historical strategy lineages have no verified
license grant; their source and adapted portions are explicitly excluded.

## Component inventory

| Component | Representative paths | Provenance | Treatment here |
| --- | --- | --- | --- |
| Project implementation and evaluation work | `src/bots/bot.py`, `scripts/`, `tests/`, `benchmarks/`, project documentation | Authored and maintained in this repository | Apache-2.0 |
| Challenge runtime and fixtures | `src/ants/`, `src/sample_bots/`, `src/tools/`, `visualizer/`, `maps/`, `submission_test/` | Google-sponsored AI Challenge 2011 source, with local modifications | Apache-2.0, retaining upstream attribution |
| Xathis Java reference | `docs/reference/xathis/` | Unchanged snapshot of Mathis Lichtenberger's first-place bot and postmortem | No verified license grant; excluded from the project license |
| Xathis Python adaptation | `src/bots/xathis_bot.py` | Taylor-authored Python integration containing constants, structures, and methods adapted from the Xathis Java source | Mixed provenance; Taylor's original portions are Apache-2.0, but adapted portions have no verified grant and the file must not be treated as wholly Apache-2.0 |
| Influence-map baseline | `src/bots/influence_bot.py` | Historical Tim Whitson strategy plus Taylor's protocol adaptation | Original portions have no verified license grant; excluded from the project license |
| Retained run artifacts | `results/current-evidence-v1/`, `statistics.json`, `parallel_statistics.json` | Generated locally from the components above | Artifact data is provided with the repository; embedded source rights do not change |
| Replay documentation image | `docs/assets/replay-current-evidence.png` | Project-generated browser capture of a retained replay rendered by the bundled visualizer | Apache-2.0 visualizer and project-generated data; exact source and method are recorded in `THIRD_PARTY_NOTICES.md` |

## Why Apache-2.0

Using the same permissive license as the upstream challenge infrastructure
keeps the project-authored modifications compatible with their source. The
root [`LICENSE`](../LICENSE) contains the standard Apache License 2.0 text, and
[`NOTICE`](../NOTICE) retains the upstream project attribution.

The upstream license basis is the challenge repository's starter-package
documentation, which states that the package and challenge code were released
under the Apache license. The exact evidence and audited source revision are
recorded in [`THIRD_PARTY_NOTICES.md`](../THIRD_PARTY_NOTICES.md).

## What the root license does not do

Publishing a license for Taylor-owned and Apache-derived work cannot grant
rights that belong to other authors. No verified license grant was found for
the Xathis reference, Xathis-derived portions of the Python adaptation, or the
original Tim Whitson strategy, so this repository does not represent those
portions as open source.

Their exact status and audit revisions are recorded in
[`THIRD_PARTY_NOTICES.md`](../THIRD_PARTY_NOTICES.md). If a future primary-source
license or author permission is found, update that notice with the evidence;
do not silently broaden the root license.

## Contributor rule

New original contributions are accepted under Apache-2.0. Do not add third-party
source, generated assets, benchmark opponents, or documentation unless its
origin and redistribution terms are recorded in `THIRD_PARTY_NOTICES.md`.

This inventory is a good-faith provenance record, not legal advice.

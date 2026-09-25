# Contributing

The repository is optimized for reproducible local work and one hosted merge
gate per pull request. A useful contribution leaves a reviewer—and a hiring
reader—able to follow the problem, the change, the validation, and the limits
of the evidence.

## Set up

```bash
git clone https://github.com/T-Py-T/ants-strategy-agent.git
cd ants-strategy-agent
uv sync --all-extras
uv run --all-extras pre-commit install
```

Use a focused branch name that describes the change. Do not commit generated
files from `game_logs/`, local environments, credentials, or editor settings.

Before choosing a larger piece of work, check the
[`OPEN_PROBLEMS.md`](docs/OPEN_PROBLEMS.md) inventory. It records scoped open
and held work, including what evidence would close an item; it is not a
readiness or acceptance gate.

## Validate locally

Run the local gate before opening or updating a pull request:

```bash
uv run --all-extras pre-commit run --all-files
make test
```

Changes to benchmark behavior should also run the smallest relevant named
match or benchmark target. Record the code revision, map, opponents, seeds,
turn cap, raw results, and limitations with any result presented as evidence.
Use the [open-problems evidence guidance](docs/OPEN_PROBLEMS.md) when a result
addresses or reduces an inventory item.

GitHub Actions intentionally runs only for pull requests targeting `main`.
Routine branch pushes should not be used as a test runner.

## Pull requests

- Keep one concern per pull request.
- Explain the bounded problem, the behavior being changed, and link its
  implementation and evidence.
- Add or update tests for executable behavior.
- Preserve historical bot behavior unless the change explicitly creates a new
  policy or fixes a demonstrated compatibility defect.
- Keep performance and win-rate claims narrower than the retained evaluation
  supports.
- State important trade-offs, limitations, and follow-up work; link follow-up
  work to the relevant entry in [`OPEN_PROBLEMS.md`](docs/OPEN_PROBLEMS.md).

## Make the work easy to review

For a contribution that should stand up to technical or hiring review, make
the path inspectable rather than relying on a headline claim:

1. State the problem and the scope of the proposed change.
2. Point to the relevant implementation and explain the key design choice.
3. Show the exact validation command and the retained result or replay when
   the change affects match behavior.
4. Call out what was not tested, what the evidence does not establish, and
   what remains open.

This keeps engineering evidence separate from a résumé-style performance
claim and gives the next contributor a clear starting point.

## Tip-cites

After a pull request is merged, record a compact pointer in the bank or the
related documentation using the [tip-cite protocol](docs/OPEN_PROBLEMS.md#tip-cite-protocol):

```text
T-Py-T/ants-strategy-agent #<PR> <8-char-merge-tip>
```

Use the first eight hexadecimal characters of the **merge commit on `main`**,
not the branch tip or an unmerged commit. A tip-cite identifies the reviewed
revision; it does not create a `READY` status or strengthen evidence that was
not retained. Never treat a merged pull request, passing checks, or a tip-cite
as a standalone `READY` claim; readiness requires the project’s stated criteria
and retained evidence.

## Licensing and provenance

Contributions are accepted under Apache-2.0. The authoritative component
boundary is maintained in [`docs/LICENSING.md`](docs/LICENSING.md). Before
adding third-party source or assets, record the origin, revision, license, and
local treatment in
[`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).

# Contributing

The repository is optimized for reproducible local work and one hosted merge
gate per pull request.

## Set up

```bash
git clone https://github.com/T-Py-T/ants-strategy-agent.git
cd ants-strategy-agent
uv sync --all-extras
uv run --all-extras pre-commit install
```

Use a focused branch name that describes the change. Do not commit generated
files from `game_logs/`, local environments, credentials, or editor settings.

## Validate locally

Run the local gate before opening or updating a pull request:

```bash
uv run --all-extras pre-commit run --all-files
make test
```

Changes to benchmark behavior should also run the smallest relevant named
match or benchmark target. Record the code revision, map, opponents, seeds,
turn cap, raw results, and limitations with any result presented as evidence.

GitHub Actions intentionally runs only for pull requests targeting `main`.
Routine branch pushes should not be used as a test runner.

## Pull requests

- Keep one concern per pull request.
- Explain the claim or behavior being changed and link its evidence.
- Add or update tests for executable behavior.
- Preserve historical bot behavior unless the change explicitly creates a new
  policy or fixes a demonstrated compatibility defect.
- Keep performance and win-rate claims narrower than the retained evaluation
  supports.

## Licensing and provenance

Contributions are accepted under Apache-2.0. The authoritative component
boundary is maintained in [`docs/LICENSING.md`](docs/LICENSING.md). Before
adding third-party source or assets, record the origin, revision, license, and
local treatment in
[`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).

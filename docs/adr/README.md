# Architecture Decision Records (ADR)

This directory is the index for Architecture Decision Records. ADRs capture
significant technical decisions, the context behind them, and the trade-offs
considered — as a planning and provenance surface, not as proof that a decision
was implemented, validated, or accepted.

## Status boundary

- This index makes **no `READY` claim**.
- An ADR documents a decision at a point in time; it does not certify
  implementation, test coverage, benchmark quality, hiring outcome, or any other
  result.
- No benchmark score, win rate, ranking, or other score is invented or implied
  here. Only results recorded in the versioned evidence packet should be cited.
- A merged pull request, passing checks, or a tip-cite records provenance only;
  it does not turn an ADR into `READY` or evidence of delivery.

## What ADRs are for

Use an ADR when a choice is:

- significant enough to revisit later (engine behavior, bot architecture,
  evaluation methodology, retention policy, licensing boundary);
- likely to be questioned by a reviewer without written context; or
- irreversible or expensive to unwind without a written record.

ADRs complement — they do not replace — code, tests, retained result packets,
and the open inventory in [`docs/OPEN_PROBLEMS.md`](../OPEN_PROBLEMS.md).

## How to add an ADR

1. Choose the next sequential number: `NNNN-short-title.md` (zero-padded four
   digits, kebab-case slug). Example: `0001-evidence-packet-layout.md`.
2. Use a short title and include at minimum:
   - **Context** — what problem or constraint prompted the decision
   - **Decision** — what was chosen
   - **Consequences** — trade-offs, follow-up work, and what was explicitly
     not decided
3. Record **status** honestly (`proposed`, `accepted`, `superseded`, `rejected`).
   Status labels describe documentation state only; they do not close inventory
   items or assert implementation.
4. Link related ADRs, open problems, and evidence paths. Do not duplicate
   benchmark outcomes — point to
   [`results/current-evidence-v1/`](../../results/current-evidence-v1/) or a
   successor packet when cited results exist.
5. Open a focused pull request. After merge, add a tip-cite entry to the bank
   below per [`GOVERNANCE.md`](../../GOVERNANCE.md) and
   [`docs/OPEN_PROBLEMS.md`](../OPEN_PROBLEMS.md#tip-cite-protocol).

## ADR index

No ADRs are listed yet. When the first record ships, add a table row with
number, title, status, and path — without inventing implementation status.

## Tip-cite bank

> Tip-cite bank: base main `8997dfe4`
> Tip-cite bank: this PR pending Steward

These lines record provenance only. The Steward resolves the 8-character tip
against `main` when a full SHA or merge context is needed. A tip-cite does not
establish readiness, benchmark quality, security, hiring outcome, or proof that
any ADR was implemented.

## Related documents

- Open and held inventory: [`docs/OPEN_PROBLEMS.md`](../OPEN_PROBLEMS.md)
- Governance and tip-cite protocol: [`GOVERNANCE.md`](../../GOVERNANCE.md)
- Planning surface: [`ROADMAP.md`](../../ROADMAP.md)

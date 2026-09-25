# Governance

This document is a thin pointer to the repository's contribution, security,
and open-problems guidance. It records provenance without duplicating project
status or evidence.

## Tip-cite

For merged work, cite the pull request and the first eight hexadecimal
characters of the merge commit on `main`:

```text
T-Py-T/ants-strategy-agent #<PR> <8-char-main-tip>
```

Use the merge commit on `main`, not a branch tip or an unmerged commit. A
short tip identifies the reviewed revision; it does not strengthen evidence
that was not retained.

## Status boundary

This document makes no `READY` claim. A merge, passing checks, or a tip-cite
records provenance only; it does not establish readiness, benchmark quality,
security, hiring outcome, or any other result. Open and held work remains so
until the evidence described in [`docs/OPEN_PROBLEMS.md`](docs/OPEN_PROBLEMS.md)
is retained.

# Support

For a focused support request, include the relevant command or reproduction,
the revision involved, and the evidence that was retained. Do not include
credentials, private keys, tokens, or other sensitive material.

## Tip-cites

A tip-cite is a compact provenance pointer for a merged change. Include the
pull-request number and the first eight hexadecimal characters of the **merge
commit on `main`**:

```text
T-Py-T/ants-strategy-agent #<PR> <8-char-main-tip>
```

Use the merge commit on `main`, not a branch tip or an unmerged commit. The
Steward resolves the short tip against `main` when the full SHA or merge
context is needed.

## Status boundary

A tip-cite records provenance; it does not make work `READY`. A merged pull
request, passing checks, or a tip-cite is not by itself evidence of readiness.
Blocked, incomplete, or untested work remains so, and this document makes no
`READY` claim or invents one.

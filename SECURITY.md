# Security policy

## Supported versions

Security fixes are applied to the current `main` branch. The repository does
not yet publish a long-term-support release line.

## Reporting a vulnerability

Email the maintainer at
[`tnt850910@aol.com`](mailto:tnt850910@aol.com) with the subject prefix
`[SECURITY] ants-strategy-agent` rather than opening a public issue. If this
repository's Security tab offers a **Report a vulnerability** button, its
private form is also an acceptable channel.

Include the affected revision, a minimal reproduction, expected impact, and
any suggested mitigation. The maintainer aims to acknowledge a report within
seven days and will coordinate disclosure after a fix or mitigation is ready.

Do not include credentials, private replay data, or other sensitive material
in issues, pull requests, logs, or retained benchmark artifacts.

This project executes locally supplied bot processes. Treat untrusted bots as
untrusted code: use a disposable environment, keep networking disabled when
possible, and do not mount credential-bearing directories into the runtime.

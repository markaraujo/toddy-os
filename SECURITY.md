# Security policy

Toddy OS is an experimental project. A foundation preview is available; the
planned desktop and assistant are not a stable product. Only the current published
preview and active development branch receive best-effort fixes. No response-time,
enterprise-support or universal hardware/security guarantee is offered.

## Report privately

Use GitHub's [private vulnerability reporting](https://github.com/markaraujo/toddy-os/security/advisories/new).
Private reporting is enabled for this public repository. Include the affected
release/commit, a minimal reproduction, impact and sanitized evidence. Do not put
credentials, private documents, account cookies or exploitable personal-machine
details in public issues or pull requests. Ordinary non-sensitive bugs can use
[the issue tracker](https://github.com/markaraujo/toddy-os/issues).

## If a credential is exposed

Revoke or rotate it with its provider immediately; deleting a line or making the
repository private does not invalidate the credential. Notify the maintainer
privately. Preserve only sanitized incident evidence, assess releases/logs/caches,
and coordinate any history rewrite with the owner. Never paste the value into an
issue, workflow log or remediation commit. Existing forks/caches cannot be erased
by a local Git cleanup, so do not claim a secret is safe merely after deletion.

## Repository controls and limits

The owner controls the protected `main` branch and CODEOWNERS review. Community
changes require PR review/checks; the exact owner account has an explicit recovery
bypass. Keep account authentication and local credential stores protected; this
repository does not configure the owner's global account or device security.

GitHub secret scanning/push protection and a pinned Gitleaks history check provide
layers of detection. Supported patterns are not all sensitive information. Private
keys, personal data, screenshots and novel credential formats still require review.
The allowlisted Pages export publishes only intended public files; it does not
sanitize arbitrary added files automatically. Review its allowlist changes closely.

PR checks use read-only token permissions, external fork runs require approval,
actions are restricted to GitHub-owned pinned revisions, and Pages deployment runs
only from `main`. Do not add untrusted `pull_request_target` execution, production
secrets in PR jobs, or automatic merge/approval tokens.

For the future OS, credential handling, owner policy/privileged executor, external
content, plugins, disk targets and package/update trust are separate boundaries.
Changes require focused failure/recovery tests in the active phase. A repository
scan does not prove an ISO or installed system has passed those runtime checks.

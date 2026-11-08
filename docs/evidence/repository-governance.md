# Open-source repository governance and public-data audit

Date: 2026-11-07. Repository: markaraujo/toddy-os, public, default branch main.
Audit base: 79eb9f422876e716e0855de6adf50918a932bb39 (246 reachable commits).
The owner requested community contributions with sole owner approval/merge control
and safeguards against sensitive-information disclosure. Visibility was not changed.

## Observed and configured server-side controls

The initial repository had no main ruleset/branch protection. Secret scanning,
push protection and private vulnerability reporting were disabled. The only
collaborator was markaraujo with admin access; no other write/admin collaborator
was found. The authenticated owner authorized the settings changes below.

| Control | Verified state after configuration |
| --- | --- |
| Main ruleset 26770413 | Active, refs/heads/main |
| Main updates/merges | Restricted to the exact owner User, markaraujo (206782379) |
| Community PR acceptance | One CODEOWNER approval, stale approval dismissal, resolved review threads |
| Required checks | check and public-content, from GitHub Actions integration 15368, branch up to date |
| History | Linear history; non-owner force pushes/deletion prohibited |
| Owner control | Exact owner always-bypass for authorized owner development/recovery; no team/app/all-admin bypass |
| Release tag ruleset 26770672 | Active for all tags; creation/update/deletion restricted to the exact owner |
| Merge methods | Squash enabled; merge commits/rebase/auto-merge disabled; merged branches deleted |
| Actions | GitHub-owned actions only; full SHA pinning required; no verified/third-party wildcard |
| Workflow default token | Read-only; workflow PR approvals disabled |
| External fork runs | Approval required for all external contributors |
| Pages environment | Only main deployment branch; deploy uses scoped pages:write/id-token:write |
| Secret scanning / push protection | Enabled for supported provider patterns |
| Private vulnerability reporting | Enabled |
| Dependabot alerts / automatic security fixes | Enabled; fixes still arrive as reviewable PRs |
| Repository / Pages secrets | Zero entries observed; no values fetched |
| Webhooks / deploy keys | Zero observed, including zero write deploy keys |

Owner approval remains a human/project authority, not a promise that GitHub
prevents the owner from bypassing their own controls. Other people can leave
review feedback, but a community change cannot substitute their approval for the
owner's CODEOWNER review or merge authority. GitHub does not permit self-approval
of one's own PR, which is why the explicit owner recovery bypass is retained.
These settings do not alter global account security, credentials or repository
visibility. Private report submission and an adversarial external-account merge
attempt were not exercised; verification read the authenticated API settings.

Non-provider generic GitHub secret patterns remained disabled after the update
request and are **not claimed enabled**. Validity checks also remain disabled.
Gitleaks supplies a separate generic-pattern check. Availability/settings can
change; audit the actual rules rather than assuming the Markdown enforces them.

## Repository files and CI

- .github/CODEOWNERS owns every path as @markaraujo, including governance/workflows.
- CONTRIBUTING.md documents fork -> focused branch -> proportional tests -> PR ->
  owner review -> squash merge, licenses and safe public contribution rules.
- SECURITY.md documents the enabled private reporting route, rotation-first leak
  response and detection/runtime limitations. CODE_OF_CONDUCT.md supplies concise
  conduct/moderation expectations. Issue/PR templates ask for sanitized evidence.
- .editorconfig standardizes UTF-8/LF and indentation without rewriting existing
  source. Dependabot checks GitHub Actions weekly with grouped reviewable PRs.
- Planning/Pages jobs have bounded execution and checkout credentials are not
  persisted. No pull_request_target or privileged fork code execution is added.
- The public-content job downloads official Gitleaks 8.30.1, checks SHA-256
  551f6fc83ea457d62a0d98237cbad105af8d557003051f41f3e7ca7b3f2470eb
  before executing, then scans history using built-in patterns. No API keys,
  admin/publishing PAT, secret-containing logs or scan reports are uploaded.
- A PR uses the base main branch's exact reviewed false-positive fingerprints,
  not an ignore list supplied by the contributor. Inline ignore comments and
  repo-supplied alternative scanner configs cannot disable this scan.
- Replaced upload-pages-artifact's nested mutable actions/upload-artifact@v4
  dependency with the equivalent Pages artifact.tar packaging and a directly
  full-SHA-pinned GitHub upload-artifact action. Only the allowlisted _site tree
  is packaged. OIDC/write authority stays confined to the main-only deploy job.

## Sensitive-content checks performed

Official Gitleaks 8.30.1 was downloaded to /tmp and its official release-asset
SHA-256 verified before execution. An initial redacted scan of all 246 reachable
commits reported 24 generic-pattern matches. Every match was reviewed without
printing credential-like values:

- Public 32-hex boot/live-test correlation UUIDs, generated in host probe scripts;
  these identify a test run and do not authenticate a service/account.
- Published 64-hex content/signing-public-key hashes and documented evidence
  hashes, including known marker-file checksums; none is a private key.

Only those exact commit/path/line/rule fingerprints are in .gitleaksignore. No
whole directory, arbitrary token field or broad key regex is suppressed. A second
history scan with those reviewed fingerprints passed: 246 commits, approximately
8.04 MB in 675 ms, no remaining findings. An independent scan of the proposed
governance/workflow files also passed. The tracked-filename check found no .env,
private-key, credential-file or image/model extension candidates.

GitHub's newly enabled secret-scanning alerts API returned zero alerts at the
observation time; its background indexing is not claimed complete. Detection of
supported patterns is not proof that no sensitive information exists anywhere.
Binary releases/ISOs and outside-Git runtime data were not re-audited by this
source-history check. Existing build/runtime security evidence remains separate.

Local scanner logs/reports stayed under /tmp/toddy-gitleaks-8.30.1 and were not
committed. No actual secret value was added to a document, issue or tool output.

## Verification and follow-through

Read back main/tag rulesets, effective main rules, workflow/action/fork permissions,
security flags, private reports, collaborators, Pages branch policy, secret counts,
hooks and deploy keys through the API. Parsed all .github YAML files locally.
Tested Pages tar construction against the current allowlisted export.

After these files are committed, verify the actual check/public-content/Pages
runs and CODEOWNERS validation on main. No OS build is required for governance.
A future leak response starts with revocation/rotation; deleting a file or rewriting
Git does not invalidate an exposed credential or erase already public copies.

## Primary references checked

- [Repository rulesets REST API](https://docs.github.com/en/rest/repos/rules)
- [GitHub security settings](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/enabling-features-for-your-repository/managing-security-and-analysis-settings-for-your-repository)
- [Secret Protection availability](https://docs.github.com/en/code-security/getting-started/quickstart-for-securing-your-repository)
- [Official pinned scanner release](https://github.com/gitleaks/gitleaks/releases/tag/v8.30.1)
- [Pinned Pages artifact implementation](https://github.com/actions/upload-pages-artifact/blob/56afc609e74202658d3ffba0e8f6dda462b719fa/action.yml)

### Publication verification completed

The owner-authorized commits were pushed through the exact-owner bypass, with
GitHub explicitly reporting the applicable protected-branch rules. On main commit
a4552eafc6b9101f9c92b3f2a039d0aa5b240292, check, public-content, Pages build and
deploy all completed successfully. Planning run 42408887762, safety run
42408887964 and Pages run 42408887750 are the recorded workflow evidence.
The CODEOWNERS errors API with ref=main returned an empty errors array.
The main ruleset readback still required owner/code-owner approval plus current
check/public-content results from GitHub Actions. A strict final local history
scan exited zero with no findings in 0.921 seconds after the three new commits.

Dependabot opened PR #1 for grouped Actions updates. It remains unmerged for
owner review; enabling dependency alerts did not grant a bot merge authority.
Playwright inspected the published README: its header uses the approved alpha-
transparent mascot and the two remaining images are labeled current design
concepts. No beige header image remains in the README.

### Phase 2 denial-text false positives — 2026-11-08 UTC

Public-content run42436373548 failed the pinned8.30.1 history scan. Local replay
with the same verified scanner archive and flags found five generic-api-key
fingerprints in historical status/dashboard outputs across b9f8f55,5b448b1 and
cdc446f. Each candidate was privately compared against the exact authored public
sentence reporting Unix socket/key access denial and graceful cleanup; every
candidate was a substring of that fixed prose, not a generated bearer credential.
No candidate values or unredacted report entered Git/log output.

Added only those five exact commit/path/rule/line fingerprints to the existing
reviewed ignore list. No rule, regex/path exemption or scanner weakening. The
strict local full-history replay then exited0 with no findings. Reports/scanner
cache stay private under.local/security/gitleaks. A new remote run must confirm
publication; previous failed runs remain failed. The latest make check passed
before this documentation/ignore-list-only change; planning references rechecked.

Phase2 source evidence produced one additional generic-api-key false positive:
safety run42440751585, commit fb35be2, B02-libxml2-build.json line58. Privately
validated the entire finding line as the testapi empty-output SHA256 (standard
empty-byte digest); no credential or arbitrary value. Added only that exact
commit/path/rule/line fingerprint, with no broad path/pattern/rule exclusion.
Pinned8.30.1 full-history replay exited0 after review. Prior failed runs remain
failed; remote confirmation follows the pushed correction.

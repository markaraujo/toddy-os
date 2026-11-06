# ADR-0057: Derive image payload selection from verified own package records

- Date: 2026-11-06
- Status: Candidate namespace inspected; full installed-payload preflight correctly refuses unfinished H07 metadata

Use actual configured Dpkg package identities and their own preserved package
records to select image payload. Verify each retained archive SHA-256 before
accepting its record, reject duplicate non-directory ownership and conflicting
shared-directory metadata, and require provenance for every selected parent.
The prepared root_inventory.py component then checks actual installed types,
file modes/UID/GID, bytes/link targets, physical parents and filesystem identity.
Package status and record hashes must remain stable throughout a successful
inspection. A mismatch fails instead of becoming an implicit release exception.

Do not copy runtime mount contents, user homes, temporary files or account/
identity values from package payload. These trees require fresh directories;
unknown package bytes under them are refused. Build-only sources/tools and
package database/cache/log data cannot be smuggled in as ordinary package files.
Generated account files remain the separate ADR-0055 input. The DBus-owned
canonical /var/lib/dbus/machine-id -> /etc/machine-id link is retained without
reading its target; other ownership, regular identity data or a different link
are rejected. Shared source directories remain physical and explicit.

The result is deliberately a package-payload candidate, not a complete image
inventory. Validated Dpkg database state, reviewed generated configuration links,
fresh accounts, the live filesystem/login profile, derived caches/indexes and
final image audits remain required. Optional QA removal must preserve package
ownership consistency through native package operations; no deletion of tracked
fixtures or credential-scan exception is introduced here.

The actual 124 installed package records form 63,132 unique selected paths,
including 60,397 regular files/symlinks. Nine fresh directory entries cover dev,
home, proc, root, run, run/dbus, sys, tmp and var/tmp. A complete 20,695,343-byte
candidate inventory is retained outside Git at
.local/logs/h10-live-root-candidate.inventory.json, SHA-256
48ca5414c1259ef0ade49f192424bcc5bc01f3f0bbcd8fb9dd336fde4f91a0ac.
Its original guest copy remains under
/mnt/lfs/tmp/toddy-root-inventory-wpymwfgc/candidate-inventory.json.
These counts describe the current source-built payload, not a finished ISO.

The native preflight verifies the retained package archives but correctly stops
at /usr/share/info/dir: its early Glibc record still owns the original bytes,
while later install-info operations have regenerated the shared index. This is
an existing final H07 metadata-closure obligation, not a new missing dependency
or permission requirement. An independent full current payload audit inspected
all 60,397 files/links and found only this mismatch, with no duplicate owners or
modified conffiles. Raw audit .local/logs/h07-current-payload-audit.json SHA-256:
1ab2907701be2e6492d8d5513c29384ae7d450ac043973140793135200bf05bb.

The already prepared upgrade_native_metadata.py + stage_package.py path builds
a new owned metadata generation without the shared Info index, then regenerates
that index after closure. Actual execution is scheduled in the final H07 driver
after Berkeley DB/APT, when the active build transaction permits it. Do not
rewrite installed metadata during the running DB suite, suppress the mismatch,
or pretend the candidate inventory passed the final preflight. Re-run the
inspection after genuine H07 closure and require a clean result.

Native candidate/refusal evidence .local/logs/h10-live-root-inventory-probe.json
SHA-256 7730235bbd019e972811888c69516ec7e9d35889b145279b75dbd2fce30e5fb1.
Prepared inventory component SHA-256:
97d4f52bbe86b8499acd488142108d11db79965aa0544e84e7dc629002966ba7.
Reproduce with python3 scripts/host/probe_live_root_inventory.py. Until the
known H07 metadata obligation is actually corrected, its nonzero result is the
expected readiness refusal, not release acceptance. Five local boundary tests
cover runtime/account exclusion, canonical DBus ownership, source parents,
shared-file conflicts and directory policy. Native inspection remains read-only
and does not synchronize active build inputs.

Alternatives rejected: selecting whole directories includes unowned state;
trusting Dpkg package count alone misses changed payload; allowing arbitrary
modified tracked files silently loses provenance; deleting the Info index from
the source hides an ownership defect. A strict candidate plus separately
reviewed generated inputs makes each release file attributable. Primary inputs
are the actual source-built Dpkg 1.22.22 package database and preserved package
manifests/archives; fresh identities/directories follow the frozen LFS 13.1
baseline and ADR-0055. Full H10/H11 execution and G1 remain pending.

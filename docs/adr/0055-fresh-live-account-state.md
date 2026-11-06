# ADR-0055: Generate fresh live-image account state from the frozen book

- Date: 2026-11-06
- Status: Native account-file component verified; image integration and login pending

A distributable root must not inherit builder passwords, the temporary tester
account, subordinate-ID allocations, root home data or machine identity. The
current native Systemd build follows LFS 13.1-systemd with sysusers=false;
inspection confirms no systemd-sysusers executable is installed. This is the
book's deliberate choice, not a missing dependency to bypass by changing the
frozen package configuration. The book creates static service identities first.

Generate fresh account files from the exact passwd/group blocks in frozen
LFS 13.1-systemd section 7.6. config/live-account-baseline.json retains those
public identities and the source/license reference, excluding the separate
build-only tester addition. The blocks match the committed H06 bootstrap.
Keep existing numeric service IDs, including messagebus 18 and Systemd network/
resolve/timesync 76/77/78. All 14 users receive locked shadow password fields;
all 34 groups receive locked gshadow fields. No age/expiry history, password
hash or builder subordinate allocation is copied. Shadow/gshadow are root-owned
0600; passwd/group are 0644. Empty subuid/subgid files and an empty 0444
machine-id are generated. The root home must be empty and becomes root-owned
0700. No login service or password bypass is enabled by this component.

scripts/build/h10/live_accounts.py operates only on a fresh caller-designated
stage. It refuses existing account/identity files, account backups, redirected
parents, tester home, root SSH/GnuPG directories and any other nonempty root
home before writing account files. It validates names, numeric relationships,
root identity, group membership and noninteractive service shells. Existing
state is preserved for diagnosis instead of reading and redacting its secrets.
The future assembly caller must enforce the H10/H11 gate and stage inventory;
this library has no installed-target migration CLI.

Alternatives: copying and editing builder passwd/shadow would import mutable
personal/security state before sanitization; calling systemd-sysusers assumes
an executable deliberately absent from this LFS edition; upgrading/rebuilding
Systemd solely for this task changes the frozen configuration unnecessarily.
The small book-derived baseline preserves source provenance and stable service
ownership. Future desktop/service accounts require reviewed baseline/recipe
additions and ownership checks. This is the foundation image baseline, not an
installer user-management implementation or a promise that all future services
are already covered.

A private native probe copied only hash-verified own Bash/False/login.defs inputs
for the account checker fixture, generated the new files and ran source-built
Shadow 4.20.2 pwck --read-only --root and grpck --read-only --root. Both exited 0
with empty stdout/stderr. It checked all lock fields, exact ownership/modes,
empty machine-id, absent tester, and refusal/preservation of an existing shadow
file, a redirected etc and a nonempty root home. The installed target account
files and Dpkg status were unchanged by hash. No account file body or existing
credential/hash is exported in the report. Successful private fixtures were
removed; failure fixtures are retained.

The initial probe had an incorrect expected count of 33 groups; the exact book
block contains 34. Both native checkers had already returned successfully. The
probe assertion was corrected from the authoritative block, without changing
the candidate baseline or dropping a checker. Original failure report SHA-256:
1251febefd470030ea922956b9d724b29dc312ec2fbd04e6d65e568b5735627a.
The failed private fixture remains /mnt/lfs/tmp/toddy-live-accounts-ierq40t7.

Final complete native report .local/logs/h10-live-accounts-probe.json SHA-256:
6008de4548dacb0c6651977c0356804952998437f6e633c703713dd313437d29.
Every report has an immutable SHA-256-suffixed copy. Tested component SHA-256:
436e78fdf2f970b6f0b9151b997559a615c8ad918b8ba7a1647531db0cde8f5c.
Baseline file SHA-256:
761ecd7d99f6e486ef6734fd41b779e6bc09a6cfab020574ee8b60f50bf60772.
Reproduce with python3 scripts/host/probe_live_accounts.py. Four local boundary
tests cover source identities, locked credentials and malformed account inputs.

Primary sources are the frozen LFS 13.1-systemd chapter07/createfiles.html
(SHA-256 f042fcc6b3389673a39fbc7c99eaca8b2589fce453d87c5b01366408af3d0867)
and chapter08/systemd.html
(SHA-256 57d4ee0f02b3aeb0be6257f276b60708dbadea3162823fe3cd2cc8456f73bb3d),
plus the actual source-built Shadow 4.20.2 read-only checker executions. Account
instructions retain the book's MIT terms in LICENSES/LFS-MIT.txt.

Actual image inventory, fresh boot identity generation, usable local live login,
service operation, whole-image credential inspection and installer owner setup
remain mandatory. An empty machine-id file is not evidence that boot generated
an identity correctly. Password locks are not a claim of a working login path.
H10/G1 remain unaccepted; no running H07 source input or installed account changed.

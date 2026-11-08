# ADR-0126: Security backports on frozen Linux-PAM 1.7.2

- Date: 2026-11-08
- Status: Accepted source preparation; native credential integration pending

BLFS13.1 freezes Linux-PAM1.7.2. The official1.7.3 release identifies subsequent
memory and authentication corrections. Preserve the frozen version, explicitly
apply the nine ordered patches in config/phase2/pam-patches.lock.json and retain
upstream authorship/licenses. Do not silently upgrade the package or import
unrelated changes to password defaults, DES removal or malformed-rule semantics.

The selected upstream commits correct pam_env buffer handling, pam_userdb timing,
pam_faillock races, pam_umask GECOS parsing and pam_time/pam_group parsing. The
pam_time day-length change requires the preceding upstream dead-negation removal:
its sole caller already handles negation. The original patch does not apply to
the frozen context without that prerequisite. GitHub's raw prerequisite transport
failed HTTP504 twice; complete previously fetched official API hunks are retained
in a transport wrapper. All three hunks apply exactly, without fuzz.

The upstream pam_unix mask correction assumes a later table without DES/BIGCRYPT.
Adapt it to the actual1.7.2 flag values, preserving all eight algorithm choices
and defaults. A named algorithm-only mask replaces the incorrect literal in the
eight entries. Enum positions are not flag values. The resulting octal mask is
014260420000; unrelated quiet/minlen bits survive all64 algorithm transitions.
The old host C fixture returns7, the adapted fixture returns0. This is a table
fixture, not a native password/module test.

A second pristine source extraction, authenticated by frozen SHA256, independently
replays all nine patches with --fuzz=0. Its eight modified files match the reviewed
tree byte for byte. Actual patch/source/fixture hashes and raw replay-log hash are
in docs/evidence/B02-pam-source-preparation.json. Native PAM, Shadow and systemd
are unchanged. Before installation acceptance require native module tests, actual
correct/incorrect password handling, deny/failure paths, helper ownership/modes,
owner/privilege/session integration and a recoverable authenticated boot. Do not
weaken generic package-mode guards for a privileged helper.

Sources: [official Linux-PAM1.7.3 release](https://github.com/linux-pam/linux-pam/releases/tag/v1.7.3)
and exact upstream commit URLs in the manifest. The earlier
[CVE2025-6020 advisory](https://github.com/linux-pam/linux-pam/security/advisories/GHSA-f9p8-gjr4-j9gx)
was fixed in1.7.1; that fact alone does not qualify1.7.2. Source applicability and
a host fixture establish neither a complete security audit nor native acceptance.

# ADR-0023: Classify Tar's observed capability display difference

- Status: Accepted classification; native installed roundtrip pending
- Date: 2026-11-06
- Scope: Frozen GNU Tar 1.35 and Libcap 2.78, LFS 13.1-systemd 8.72

## Actual result and decision

The unchanged complete suite ran all 244 groups: 223 passed, 20 skipped and
only group 233 (capabilities: binary store/restore) failed. Raw make exit is 2;
no installed paths changed. The sole diff is expected `dir/file = cap_chown=ei`
versus actual `dir/file cap_chown=ei`. Libcap 2.78 progs/getcap.c prints filename
and cap_to_text result with a space; the test's plus-to-equals normalization
does not accommodate this format. No missing capability was observed.

A separate guarded native probe with the compiled Tar archived/extracted a
real security.capability xattr and compared its original/restored bytes exactly.
It passed, and getcap reported cap_chown=ei. This measured cause is a display
expectation mismatch. The book identifies this exact test as a possible failure
and discusses absent SELinux, but that generic explanation is not the observed
cause here. SELinux tests are explicitly skipped, not claimed passing.

Retain the entire unmodified upstream test and raw failure. A strict classifier
requires all 244 unique group outcomes, exact 223/20/one-failure summary, only
233 failing and exactly the two observed diff lines. Reject unknown outcomes,
missing/duplicate groups, changed capability values and unexpected raw exits.
After classification, stage/install without changing the compiled source and
require actual installed Tar ACL plus exact capability-byte roundtrips. Native
acceptance does not re-label the upstream result all-pass.

## Alternatives and consequences

Removing the test, changing its expected result or ignoring make failure would
hide the original observation. Upgrading frozen Tar/Libcap is unnecessary.
Classification plus an independent binary-xattr postcondition directly tests
required behavior while retaining evidence of the test incompatibility.

## Sources

Frozen LFS 13.1-systemd section 8.72, actual tests/capabs_raw01.at and full raw
suite output, frozen Libcap 2.78 progs/getcap.c. Evidence lives in the target
/sources/evidence/h07-tar and full dispatcher records, copied outside Git.

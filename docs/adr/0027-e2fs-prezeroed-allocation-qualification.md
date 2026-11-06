# ADR-0027: Qualify the measured E2fsprogs allocation-count mismatch

- Status: Source-qualified complete suite; native installed roundtrip pending
- Date: 2026-11-06
- Scope: Frozen E2fsprogs 1.47.4, LFS 13.1-systemd section 8.82

The complete make check reports 393 successes and only
m_assume_storage_prezeroed failing; raw make exit is 2 and installed changes
zero. The frozen book explicitly identifies this test as known to fail. Actual
source creates two sparse 16 MiB files, attaches disposable loop devices and
compares allocated-sector counts after mke2fs with/without the prezeroed option.
The normal case meets >10000 sectors; the optimized case allocates 232 instead
of the expected 224, one additional 4 KiB block. Both mke2fs calls succeed, and
the test detaches its own loops and deletes its fixtures.

Retain raw logs, failure diff and unmodified test. Strict classification accepts
only the complete 393/one summary, the exact single failed identity and measured
>10000/232 versus >10000/224 allocation difference. Other test failures, partial
output, process failures or changed output stop installation. Do not report the
upstream suite all-pass or change its expected allocation to 232.

After staging/installing the unchanged compiled package, require default ext4
creation in an explicitly created regular file, e2fsck, mount/write/unmount,
recheck, remount and exact persistent payload verification. The cleanup removes
only its own fixture, after successful unmount. No physical disk is involved.
The graphical installer must use normal mke2fs initialization; do not enable
assume_storage_prezeroed without separately proven storage guarantees. Complete
installed-disk/ISO boot acceptance remains H12/B12/B13.

Sources: frozen LFS 13.1-systemd section 8.82; actual upstream
 tests/m_assume_storage_prezeroed/{script,expect}, build/tests/*.failed and
full check log in the designated target. No source/version/test is changed.

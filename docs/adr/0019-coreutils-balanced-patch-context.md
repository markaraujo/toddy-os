# ADR-0019: Balance Coreutils i18n patch context without changing its result

- Status: Accepted context correction; native Coreutils build/tests pending
- Date: 2026-11-06
- Scope: H07 frozen Coreutils 9.11 and coreutils-9.11-i18n-1.patch

## Diagnosis and controlled comparison

The first recipe rejected one hunk before configuration, with zero installed
changes. The sort initialization hunk has three prefix context lines but only
two suffix lines. GNU Patch 2.8's bundled manual specifies end-of-file matching
for hunks with more prefix than suffix context after fuzz. The unchanged hunk
is inside main, not at the end of sort.c, so our explicit --fuzz=0 rejects it.
All surrounding source context actually matches at a one-line offset.

Two independent fresh source trees were extracted only after archive SHA-256
verification. The original book command/default fuzz applies with exit zero,
reporting fuzz 1 for hunk 31. A context-balanced variant adds the exact next
existing source line, '  {', and adjusts the hunk's old/new line counts from
5/28 to 6/29. It applies with --fuzz=0, exit zero and no rejects. All nine
patched C/test files are byte-identical between the two trees. Logs and per-file
hashes are retained at .local/logs/h07-coreutils-compatibility.

## Decision and alternatives

Freeze the attributed context-only variant before actual compilation. Keep
all original added/removed C/test lines, the frozen Coreutils version and the
original parent patch. Do not ignore a failed hunk or omit the multibyte
initialization. Preserve the original partial source/reject and failed record,
then rebuild from a newly verified extraction; no compilation had completed.
Run all root and unprivileged expensive tests, then native ACL-preserving copy
and hashing checks before package acceptance.

Using GNU Patch's default fuzz follows the book and produces the intended
result, but balanced full context preserves our stricter matching and makes
the placement explicit. Dropping the hunk would leave function-pointer
initialization incomplete. Upgrading Coreutils or changing its C implementation
is unnecessary. This change does not alter the book's resulting program,
remove tests or relax any test result criterion. Existing LFS warnings about
other i18n-patch bugs still apply; a matching patch is not proof of correctness.

Derived patch SHA-256:
9a6444bc07dea6c37be682fd7c3ddd3707250a0850eba3ca342d6c84bb90f8e6.

## Primary sources

- Frozen [LFS 13.1-systemd 8.61 Coreutils](https://www.linuxfromscratch.org/lfs/view/13.1-systemd/chapter08/coreutils.html).
- The exact Coreutils 9.11 source and i18n parent patch in config/sources.lock.json;
  parent SHA-256 7c2aecf9ae24b87b019595e382b9f41d2c96de7f95abe95ad8cacc7e2ce1bbcc.
- GNU Patch 2.8 patch.man in the frozen patch-2.8.tar.xz archive, matching the
  actual temporary patch executable version; sections on fuzz and asymmetric
  prefix/suffix context. Runtime code and tests were inspected directly.

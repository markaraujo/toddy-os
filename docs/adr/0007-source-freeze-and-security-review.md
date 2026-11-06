# ADR-0007: Freeze edition inputs and track security remediation explicitly

Date: 2026-11-05
Status: Accepted

## Decision

Freeze the official LFS/BLFS 13.1-systemd book archives and all 94 inputs of
LFS's wget-list-systemd. Require the book's MD5 plus an observed SHA-256 before
extraction. Preserve upstream and actual download URLs independently. This
run used the exact published URLs without mirror substitutions.
Book archive hashes and errata snapshots are in config/books.lock.json;
source hashes are in config/sources.lock.json. Retrieval over upstream HTTPS
and comparison with the book are verified; detached signature verification
and byte-identical reproducibility are not claimed.

The edition's errata page reports no miscellaneous corrections, but it links
to obsolete advisory landing pages. Follow their link to the current combined
advisory application and query release 13.1. Save that result and its hash.
A frozen book is not evidence of a vulnerability-free distribution.

Do not silently replace the book's compiler/libc or package versions during
toolchain construction. Keep an explicit security remediation register. Before
final release, review upstream patches/backports for installed components,
freeze each additional source with integrity data and record the deviation
and regression tests. A final recipe must not mistake this baseline freeze
for a security approval. Resolve critical/high affected release components
before declaring the release usable; document remaining assessed limitations.

## Initial security register

The current release-13.1 query includes advisories for Python, patch, Vim,
Expat, util-linux, PCRE2, glibc, Xz and OpenSSL in the baseline source list.
In particular, sa-13.1-044 concerns Python 3.14.7 and sa-13.1-043 concerns
Glibc 2.44. Inspect exact patch coverage, not just a patch's filename.
H07 must assess/backport core fixes; desktop dependency selection must assess
its own advisories before B02. No updated package version has been selected
or claimed installed by this ADR. This register is an unresolved release
obligation, not permission to omit fixes.

## Alternatives and consequences

A moving stable book or unrecorded upgrades break repeatable recovery.
Freezing without checking current advisories hides known vulnerabilities.
An explicit baseline plus versioned, tested security overlays retains the
book's integration guidance and makes release deviations reviewable.
MD5 alone is inadequate as an authenticity claim; SHA-256 pinning prevents
subsequent content changes but is not an independent publisher signature.

## Sources

- LFS 13.1-systemd downloaded archive, sections 2.2, 3.1–3.3 and preface errata.
- [LFS 13.1 errata](https://www.linuxfromscratch.org/lfs/errata/13.1-systemd/) and [BLFS 13.1 errata](https://www.linuxfromscratch.org/blfs/errata/13.1-systemd/), observed 2026-11-05.
- [Current security advisory application](https://www.linuxfromscratch.org/advisories/), release 13.1 query observed 2026-11-05. Snapshot SHA-256: aa562da21adbfa442f88404b029242eea2d24ac04fa4b4eefff4eb819a304de1.

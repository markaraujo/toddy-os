# ADR-0010: Pin security maintenance releases before final recipes

Date: 2026-11-05
Status: Selected/frozen inputs; compilation and regression acceptance pending

## Decision

For the final H07 packages, explicitly replace Xz 5.8.3 with 5.8.4,
OpenSSL 4.0.1 with 4.0.3 and Python 3.14.7 with 3.14.10. Keep their original
book inputs in the baseline lock, keep compiler versions and Glibc version
unchanged, and record each replacement in security-overlay.lock.json. These
are same-branch security maintenance choices, not build-failure workarounds.
No moving latest URL is used. Book flags/order still apply, with versioned
paths and upstreamed patches reviewed for the selected sources.

The release sources matched publisher-provided SHA-256 values: Python's
release page, OpenSSL's checksum file and Xz's GitHub release-asset digest.
Xz's archive and detached signature were downloaded; its official public-key
endpoint returned HTTP 403. PGP verification is explicitly unclaimed. Hash
pinning/integrity verification passed. No account or security policy was
changed to retrieve the public inputs.

Run the book's tests and actual runtime checks before accepting any package.
Python must demonstrate working SSL against selected OpenSSL; inspect whether
the old 3.14.7 OpenSSL-4 patch is already upstream rather than force-applying
it. The temporary Python remains build infrastructure until the final
source-built maintenance version replaces it. No security fix is claimed
installed merely because inputs are pinned.

## Alternatives and consequences

Shipping the identified vulnerable baseline is unsuitable. Jumping to Python
3.15 or OpenSSL 4.1 adds unrelated compatibility scope. Maintaining our own
individual backports where upstream offers supported maintenance releases
adds integration burden. Exact maintenance releases preserve branch scope,
but still require all source/license tracking and regression checks. Other
advisories remain unresolved release obligations.

## Primary sources, observed 2026-11-05

- [XZ 5.8.4 announcement and security advisory](https://tukaani.org/xz/): decoder reinitialization fix; same 5.8 branch.
- [OpenSSL download/support table](https://openssl-library.org/source/): 4.0.3 is the maintained 4.0 release; checksum linked by publisher.
- [Python 3.14.10 release](https://www.python.org/downloads/release/python-31410/): expedited security maintenance, certificate distrust and tarfile/cookie fixes; source SHA-256 published.
- LFS release-13.1 advisory snapshot in ADR-0007 identifies the baseline exposure.

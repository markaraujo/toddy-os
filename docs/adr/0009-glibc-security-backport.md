# ADR-0009: Final Glibc 2.44 stable security backport

Date: 2026-11-05
Status: Accepted inputs; compilation and critical-suite acceptance pending

## Decision

Keep Glibc 2.44 and the frozen LFS 13.1-systemd edition. For its final H07
build only, replace upstream_fixes-1 with the official LFS
upstream_fixes-3 bundle, SHA-256
cd3245887c9c2564ef18b8e9ed4046093a575fc91bce00fd82eb931102e4a30e.
Do not apply both bundles. The original baseline lock and temporary builds
remain unchanged. The explicit overlay is config/security-overlay.lock.json.

The published bundle covers the six vulnerabilities of sa-13.1-043 and
identifies upstream stable commits, one master cherry-pick and one approved
mailing-list patch. Applicability of all 49 sequential patches was tested
on the exact frozen source plus FHS patch. This is not an acceptance waiver:
run the complete critical libc suite before installing the final package,
retain raw results and reject unexplained failures. Only the exact
io/tst-lchmod failure documented by frozen LFS section 8.5 for this chroot may
be classified expected without further investigation.

## Alternatives and consequences

Leaving the known-vulnerable baseline in the release is unacceptable.
Retargeting a new Glibc version adds unnecessary integration risk. The
published stable patch keeps ABI/version scope while making deviations
explicit. Input pinning is an observed HTTPS SHA-256, not an independent
signature claim. Other baseline advisories remain unresolved release work.

## Sources

- Frozen LFS 13.1-systemd section 8.5: critical suite and chroot failure note.
- [LFS Glibc patch bundle](https://www.linuxfromscratch.org/patches/downloads/glibc/glibc-2.44-upstream_fixes-3.patch), retrieved 2026-11-05.
- [Current LFS advisories](https://www.linuxfromscratch.org/advisories/), release 13.1 query, sa-13.1-043; snapshot and applicability evidence in ADR-0007.

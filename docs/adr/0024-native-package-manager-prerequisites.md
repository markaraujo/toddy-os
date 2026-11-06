# ADR-0024: Freeze native package-manager prerequisites

- Status: Source candidates verified/frozen; native builds pending
- Date: 2026-11-06
- Scope: Additional H07 source-built Dpkg/APT dependencies

## Decision and evidence

Dpkg 1.22.22 configure requires Libmd; APT 3.0.4 CMakeLists.txt unconditionally
requires Berkeley DB and XXHash. GoogleTest supports the real APT unit suite.
Select Libmd 1.3.0, XXHash 0.8.4, GoogleTest 1.18.0 and Debian-maintained Berkeley
DB 5.3.28+dfsg2-12 source/patch series. These are new supplemental components,
not silent upgrades of an already built/frozen target package. Preserve the
full patch series, provenance and notices. No Debian binary or maintainer
script is imported, and foreign binary repositories remain forbidden.

Libmd's upstream announcement SHA-256, GoogleTest's publisher release-asset
SHA-256 and both DB source DSC hashes match actual downloads. XXHash's official
maintainer release archive is HTTPS-fetched and observed-SHA pinned; no published
archive digest or independent signature is claimed. Complete hashes/sizes/URLs
are in supplemental-sources.lock.json and candidate verification JSON outside
Git. DB original archive SHA-256 is
ad41b507415dec8316e828b2230242af2251d2c86eefa3c7aa9ef47c5239ef33;
Debian patch archive is
ced49fb5af63eeef6f4edd603903a8ec22e0a598b570eac99e97652c82e8c433.

Inspect/apply DB patches as source changes only, including CVE-2017-10140,
CVE-2019-8457 and compiler fixes. Do not run Debian package maintainer scripts.
Verify strict application and complete applicable tests before installing.
Native package-manager unit, signed-index, solver, tamper rejection and rollback
checks remain mandatory; verified source downloads do not satisfy them.

## Signing dependency resolution

ADR-0026 resolves the source transport failure through the responsive official
FTP hostname's /ftp/gcrypt/ HTTPS path and verifies all detached signatures.
The older advertised mirror directories were stale. GnuPG 2.5.24 and its
support libraries are now separately frozen, with security rationale and native
build/test obligations retained there. No unauthenticated fallback was accepted.

## Alternatives and consequences

Disabling APT's unconditional Berkeley discovery is unsupported by current
source. Importing Debian binary libraries would violate the source-built base.
A different package-manager design would discard the measured D03 ownership
prototype without need. Maintained DB 5.3 source/patches retain compatible
upstream licensing; later relicensed Berkeley editions are not silently used.

## Primary sources

- Actual frozen Dpkg configure.ac and APT CMakeLists.txt.
- [Libmd 1.3.0 announcement](https://archive.hadrons.org/software/libmd/libmd-1.3.0.announce).
- [XXHash 0.8.4 release](https://github.com/Cyan4973/xxHash/releases/tag/v0.8.4).
- [GoogleTest 1.18.0 release](https://github.com/google/googletest/releases/tag/v1.18.0).
- [Debian DB source descriptor](https://deb.debian.org/debian/pool/main/d/db5.3/db5.3_5.3.28+dfsg2-12.dsc).
- [GnuPG releases](https://www.gnupg.org/download/),
  [release fingerprints](https://www.gnupg.org/signature_key.html) and
  [listed mirrors](https://gnupg.org/download/mirrors.html).

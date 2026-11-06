# ADR-0017: Freeze CMake support inputs before the native package manager

- Status: Sources selected and verified; builds/tests pending
- Date: 2026-11-06
- Scope: Source additions after the complete frozen LFS base, supporting ADR-0012

## Decision

Freeze CMake 4.4.2 and Libuv 1.52.1 from BLFS 13.1-systemd, with explicitly
reviewed Curl 8.23.0, Libarchive 3.8.11 and Nghttp2 1.71.0 support libraries.
Exact URLs, sizes, SHA-256, book comparison versions and authentication basis
are in config/supplemental-sources.lock.json. No baseline LFS archive/version
changes. No support input is built or installed by this decision.

Prefer these separately packaged system libraries when building CMake, using
the frozen BLFS --system-libs recipe. Retain and inventory the book's explicitly
bundled JsonCpp/cppdap/librhash sources and notices; do not claim they disappear
just because the other libraries are external. Verify actual build configuration,
linkage, complete applicable suites and native CMake project execution before
accepting the packages. Preserve an explicit component/license inventory.

## Evidence and alternatives

CMake and Libuv archives match the frozen BLFS MD5 values and observed SHA-256.
CMake also matches its official SHA-256 manifest. Libuv has a detached signature,
but no independent OpenPGP verification is claimed. A guessed SHASUMS256.txt
URL returned 404; no digest was invented. The official dist index and source
archive were retrieved successfully. This does not modify workstation trust.

The book's Curl 8.21.0 has published upstream security defects, including the
HTTP/2 upload use-after-free CVE-2026-92392. Upstream's 8.23.0 vulnerability
table lists no published issues at this check. That is a time-bound observation,
not a claim of absence of undiscovered bugs. Select the current maintenance
release rather than introduce known defects before any build. Libarchive's
October 30 release identifies 3.8.11 as a security and bugfix release. Nghttp2's
November 2 release includes protocol length/window and integer-overflow bounds
fixes; selecting it avoids introducing those known correctness defects in a
new HTTP/2 client library. Do not describe these Nghttp2 changes as assigned
CVEs without evidence. Their publisher release-asset SHA-256 values match the
source archives downloaded over official HTTPS; OpenPGP is not independently
verified. Older book archives are retained as unselected research inputs only.

Using CMake's older bundled network/archive libraries would obscure their
update/ownership boundaries. Blindly advancing every book component to latest
would add unrelated changes; CMake 4.4.2 and Libuv 1.52.1 remain the selected
book inputs. These are explicit additive selections before first use, not a
silent version change to bypass a failing build.

## Primary sources checked

- Frozen BLFS 13.1-systemd sections general/cmake, general/libuv,
  general/libarchive, basicnet/curl and basicnet/nghttp2; book hashes in config/books.lock.json.
- [Official CMake 4.4.2 SHA-256 manifest](https://cmake.org/files/v4.4/cmake-4.4.2-SHA-256.txt).
- [Official Libuv 1.52.1 dist directory](https://dist.libuv.org/dist/v1.52.1/).
- [Curl 8.21.0 issues](https://curl.se/docs/vuln-8.21.0.html),
  [Curl 8.23.0 issues](https://curl.se/docs/vuln-8.23.0.html),
  [8.23.0 publisher assets](https://github.com/curl/curl/releases/tag/curl-8_23_0).
- [Libarchive 3.8.11 release/assets](https://github.com/libarchive/libarchive/releases/tag/v3.8.11).
- [Nghttp2 1.71.0 release/assets](https://github.com/nghttp2/nghttp2/releases/tag/v1.71.0).

Retrieved metadata and source checks are retained outside Git under
.local/upstream-verification and .local/sources. These additions do not yet
complete the other APT/dpkg build dependencies or native package-manager tests.

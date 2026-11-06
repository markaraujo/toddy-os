# ADR-0012: Freeze stable native package-manager sources

Date: 2026-11-06. Status: accepted source selection; build/test acceptance pending.

## Decision

Build dpkg 1.22.22 and APT 3.0.4 from source after the frozen LFS base.
Pin their complete source archives in config/supplemental-sources.lock.json;
these are additions implementing ADR-0008, not replacements for baseline LFS
packages. Do not import Debian/Ubuntu binary packages into the target.
Builder dpkg remains a separately recorded development tool.

The actual downloaded source archives match SHA-256 and sizes published in
Debian's corresponding DSC files over official HTTPS. DSC hashes/URLs are
pinned too. OpenPGP signatures are not independently verified; no signature
verification claim is made. Archive integrity is enforced before extraction.
The source hashes and checksum origin are reproducible, not moving latest URLs.

## Evidence and alternatives

The official Debian security tracker identifies dpkg 1.22.22 as the trixie
version, fixing CVE-2026-2219 (malformed zstd stream denial of service). It
identifies APT 3.0.4 as the trixie security update fixing CVE-2026-109518
(redirect/retry hard-link reuse could install unverified payloads). Selecting
APT 3.0.3 would retain that known issue. Sid versions 1.23.11/3.3.6 add churn
unneeded for this initial native integration. Copying builder binaries would
violate source/component ownership and libc compatibility requirements.

Primary sources consulted on 2026-11-06:

- https://deb.debian.org/debian/pool/main/d/dpkg/dpkg_1.22.22.dsc
- https://deb.debian.org/debian/pool/main/a/apt/apt_3.0.4.dsc
- https://security-tracker.debian.org/tracker/source-package/dpkg
- https://security-tracker.debian.org/tracker/CVE-2026-2219
- https://security-tracker.debian.org/tracker/source-package/apt
- https://security-tracker.debian.org/tracker/CVE-2026-109518
- Actual verified source README/debian/control and APT 3.0.4 CMakeLists.txt.

## Consequences and required verification

Source inspection establishes additional dependencies, not a working package
manager: dpkg needs libmd plus the book compression libraries; APT needs CMake,
Berkeley DB, OpenSSL, xxHash and test tooling, with optional/system integration
libraries assessed explicitly. Freeze these inputs before use, prefer the
selected BLFS edition when it supplies the package, and retain source/license
notices and actual unit/integration results. Do not disable package integrity
checks or remove failing tests to make the integration appear complete.

Use an explicit project keyring with Signed-By and authenticated Release/
InRelease metadata. Never use a keyring download URI or legacy apt-key network
key retrieval: the tracker still lists CVE-2011-3374 as unimportant/unfixed,
not exploitable in Debian without a keyring URI. Toddy must verify its actual
configuration, not infer immunity just from the selected version. Test altered
indexes/payloads/signatures, dependency ordering, upgrade/conflict/conffile
behavior and controlled recovery in the disposable guest before G1. Keep all
private signing material outside Git, images and logs. This ADR does not claim
APT, native dpkg, a signed repository or release update recovery already works.

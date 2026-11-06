# ADR-0013: Freeze security sources for the remaining native base

Date: 2026-11-06. Status: accepted source selection; builds/tests pending.

## Decision and source evidence

Retain the original LFS/BLFS 13.1-systemd baseline and compiler versions.
Explicitly select these additions in config/security-overlay.lock.json:

| Component | Selected source | Reason |
| --- | --- | --- |
| GNU Patch | 2.8.1 | LFS sa-13.1-087: reverse-patch path traversal and malformed-patch faults |
| Vim | 9.2.1201 | LFS sa-13.1-065/086: script/plugin code injection fixes |
| Expat | 2.10.0 | Earlier 2.8.4/2.8.5/2.9.0 fixes plus four newer upstream security fixes |
| util-linux | 2.42.4 | LFS sa-13.1-048: complete mount/path/helper fixes and additional bounds/descriptor fixes |

The full frozen LFS advisory snapshot is already pinned in books.lock.json.
Upstream review found a newer Expat release than that snapshot. Its verified
Changes and maintainer announcement identify fixes for CVE-2026-113351,
CVE-2026-115506, CVE-2026-117610 and CVE-2026-118370. Expat 2.9.0 was downloaded
for inspection only; 2.10.0 is the selected build input. This choice is a
recorded security change, not a moving latest dependency or build-error bypass.
The shared-library SONAME remains libexpat.so.1; API/build compatibility still
requires actual package and downstream tests.

## Integrity experiments

All four archives downloaded and have pinned observed SHA-256. Expat matches
the publisher's GitHub asset digest; util-linux matches upstream published
sha256sums.asc. GNU Patch's detached signature verified with gpgv against the
GNU public keyring, signing fingerprint
259B3792B3D6D319212CC4DCD5BF9FEB0313653A. Direct ftp.gnu.org access failed;
the trusted kernel.org GNU mirror supplied archive, signature and keyring.
No TLS checks or network controls were disabled. The keyring hash is pinned.

Vim's annotated tag object and commit are pinned; GitHub's API reports the
tag signature valid. Archive OpenPGP verification is not independently claimed.
The verified source contains the cargo compiler-plugin escaping correction.
The original book also uses a GitHub source archive with observed integrity.
No independent OpenPGP claim is made for util-linux's signed sums either.

## Remaining Expat risk and consequences

Do not claim Expat is free of known issues. Its source and upstream issue
#1160 explicitly retain unresolved, partly non-public reports including
CVE-2025-66382. The frozen advisory's statement that CVE-2026-66046 remains
unfixed conflicts with the actual upstream Changes: that specific attribute
lookup issue is listed fixed in 2.8.4. Preserve the distinction; other upstream
issues remain unresolved. The 2.10.0 maintainer announcement likewise states
that unresolved reports remain. Source selection alone is not risk acceptance
or proof of runtime mitigation.

Before release, assess actual XML-consuming services/tools and verify bounded,
unprivileged processing of untrusted XML (time/memory/size and entity policy),
with malformed/expansion regression tests where applicable. Keep this risk in
open decisions and known limitations; do not substitute an obsolete library
or turn off required functionality to conceal it. No NDA or paid upstream
support is required to continue independent implementation.

Every selected package must still compile, pass its actual suite and native
postconditions, retain corresponding sources/licenses and complete dependency
closure. These selections have not yet been built in the final target.

Primary upstream sources consulted on 2026-11-06:

- https://api.github.com/repos/libexpat/libexpat/releases/tags/R_2_10_0
- https://blog.hartwork.org/posts/expat-2-10-0-released/
- https://github.com/libexpat/libexpat/issues/1160
- https://mirrors.edge.kernel.org/pub/linux/utils/util-linux/v2.42/sha256sums.asc
- https://mirrors.kernel.org/gnu/patch/patch-2.8.1.tar.xz.sig
- https://mirrors.kernel.org/gnu/gnu-keyring.gpg
- https://api.github.com/repos/vim/vim/git/ref/tags/v9.2.1201
- Corresponding downloaded source Changes/runtime files and pinned LFS snapshot.

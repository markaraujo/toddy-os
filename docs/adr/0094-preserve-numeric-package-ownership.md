# ADR-0094: Preserve numeric ownership when extracting native metadata inputs

- Date: 2026-11-07
- Status: Implemented; native closure retry in progress
- Extends: ADR-0039 build-user normalization; does not change its allowed identities

## Failure and decision

Final metadata closure completed 14 packages, then correctly refused CMake's
/usr/share/doc/cmake/Licenses with unreviewed owner/group 18:18. The accepted
predecessor component record and installed original directory have 101:101,
the target tester identity. The bootstrap builder's user name for numeric 101
was messagebus; inside the target messagebus is numeric 18. Native dpkg-deb
--raw-extract resolved the archived name and changed the effective identity
before the existing numeric build-user normalization could run.

Extract the hash-verified own archive data using native dpkg-deb --fsys-tarfile
and native tar --numeric-owner --same-permissions, then extract control data with
dpkg-deb --control. Preserve all numeric IDs and reviewed privileged modes.
The existing ownership policy still validates the entire stage before changes,
normalizes tester 101 to root, and rejects unreviewed service/privileged owners.
Do not whitelist messagebus-owned CMake documentation, change a system account,
relax the ownership check or alter the preserved original archive.

Alternatives: restoring ownership from the component record after ordinary
extraction adds another metadata rewrite; numeric extraction preserves the
archive's original IDs directly. A blanket root-owner extraction would erase
legitimate reviewed service groups/setgid helpers and is rejected.

The failed staging tree is preserved under
/mnt/lfs/sources/recovery/metadata-cmake-numeric-7g9_17_1. CMake remained version
4.4.2-1; no revised CMake archive was created or installed. Earlier 14 completed
metadata generations are retained and skipped only after their actual version,
policy/provenance and dependency checks pass. Raw failed closure log SHA-256:
3580b99fa25070161535b95b751d08f1c692cecef51c29a8823a658649db5185.

Sources: actual accepted CMake 4.4.2 native archive/component inventory, target
passwd identities, native Dpkg 1.22.22 extraction and GNU tar numeric ownership
semantics; the frozen reviewed ownership_action policy and its CMake/privileged
helper negative controls. This changes extraction identity resolution, not any
package source, feature or acceptance requirement.

## Native retry result and existing-directory follow-up

Numeric extraction passed for CMake: 4.4.2-1+toddy1 was packaged and installed,
with the Licenses directory recorded as root:root and the unchanged policy
normalizing original 101:101 correctly. Native metadata closure advanced beyond
CMake; no new ownership exception was added.

Inspection also found native Dpkg preserves the pre-existing installed directory
owner (101:101) during replacement, even when the revised archive records 0:0.
Prepare a final reconciliation of only owned directories whose complete provider
set agrees on the expected numeric identity and whose actual difference is the
reviewed tester identity. Validate the entire set before changing any directory,
retain intent/result receipts and preserve modes; reject redirected paths,
conflicting providers and unreviewed owners. Future fresh image assembly already
uses the corrected archive metadata, but the build target must also be verified.
This final reconciliation remains pending while the serial metadata upgrade runs.

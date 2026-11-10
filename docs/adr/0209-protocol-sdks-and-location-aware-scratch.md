# ADR-0209 — Protocol SDKs and location-aware package scratch

Status: accepted for the scoped B02 implementations below.

## Context and decision

Linux Control Center requires ModemManager; its default MBIM/QMI backends need
the frozen BLFS13.1-systemd libmbim1.34.0 and libqmi1.38.0. Preserve those
backends, full QMI collection, introspection and upstream root-only device
authorization. Use the frozen book's QRTR-disabled switch. No device, firmware
operation, cellular service or Settings GUI is accepted by local protocol tests.

The target's fixed16GiB reserve cannot accommodate large expanded sources and
duplicate native archive/staging work. Reuse the already allocated Doxygen
scratch, with its recorded UUID and a root0700 private parent. Permit only exact
frozen libqmi, ModemManager and Control Center source identities. Authenticate
the archive, complete source fingerprint, inode and read-only alias; a root write
must fail EROFS. Compiler workers receive only their own source/work views.
Original Doxygen cache bytes remain unchanged. No new volume or reserve reduction.

Native archive construction may use a root0700 workspace on that same scratch.
Promotion keeps the existing canonical /sources/stage guard through verified bind
aliases. Installed payload still lands on the target filesystem. Budget target
4KiB allocation conservatively, including directories, links and empty files,
plus8MiB metadata above16GiB. Reject special files. Separately budget scratch
promotion/archive copies and the archive-cache filesystem. Retain full-root
before/after verification for these unqualified recipes under ADR-0110.

## Actual validation and limits

[Libmbim](../evidence/B02-libmbim-install.json) installed0/0 after nine original
programs/131cases; installed local C/GI/CLI refusal and recovery checks passed.
[Libqmi](../evidence/B02-libqmi-install.json) installed after seven original
programs/122cases. Initial physical staging path was correctly refused by the
canonical guard, changed0. Corrective canonical installation succeeded but its
own GI probe assumed an absent Message record. Actual installed GIR ClientDms
type/inheritance corrected a verify-only run0/0/changed0; no reinstall.

[Source alias qualification](../evidence/B02-libqmi-scratch-input.json) includes
actual same-boot read-only unmount/remount recovery.
[Native placement](../evidence/B02-native-scratch-placement.json) includes actual
same-boot workspace unmount/remount/private write/read/cleanup and the completed
libqmi transaction. Cold restoration code is prepared, but this slice does not
claim a new cold boot, full-system recovery, physical hardware or GUI acceptance.
Closed promotion data remains recoverable without auto-restoring its alias.

Three source-boundary tests and four allocation/workspace-boundary tests extend
the repository suite to331 passing tests. Native evidence comes from the actual
guest separately; unit tests alone do not establish mount/runtime acceptance.

# ADR-0050: Mtools for GRUB EFI image construction

- Date: 2026-11-06
- Status: Source verified/frozen; native build, FAT roundtrip and ISO boot pending

The frozen GRUB 2.14 util/grub-mkrescue.c invokes mformat and mcopy when
constructing its EFI FAT image (lines 858–864). These programs are absent from
the accepted base. Use source-built GNU Mtools as an additional H11 dependency;
no frozen baseline package is upgraded. Reimplementing FAT construction or
using builder-distribution tools would add avoidable divergence from the
selected GRUB path. This does not replace actual BIOS/UEFI ISO tests.

Primary sources are the frozen GRUB source, GNU's
https://ftp.gnu.org/gnu/mtools/ release directory and the signed 4.0.50 archive:
https://ftp.gnu.org/gnu/mtools/mtools-4.0.50.tar.bz2 . Upstream NEWS reports a
CVE-2026-118384 fix in this release; no independent vulnerability regression
has yet been performed. The additional component is selected before its first
native build. The GNU project landing page timed out; the official FTP-over-
HTTPS archive, signature and keyring were retrieved successfully.

Archive SHA-256 f3a58e6cfc2634b03c240442548e3b00103692357afc28e1e7104744dd6478b5,
465818 bytes. All 198 tar members passed the existing safe-source filter.
Detached signature verification with gpgv exited zero and returned VALIDSIG
51A23D9D7C4DF41AA48FA893E99CF5537790B839 (Alain Knaff). The key was scoped to
https://ftp.gnu.org/gnu/gnu-keyring.gpg, downloaded over HTTPS; its observed
SHA-256 and the detached signature hash are frozen in the supplemental lock.
This establishes signature verification against that GNU-published keyring,
not an independent personal identity or web-of-trust certification. No global
trust settings changed. Raw downloads, verification and source excerpts are
outside Git under .local/upstream-verification/mtools.

The original COPYING and mformat/mcopy headers specify GPL version 3 or later;
the manual/INSTALL documentation specifies GFDL 1.3 or later without invariant
sections or cover texts. Preserve per-file notices and complete terms. This
source inventory is not completion of the release legal audit.

The distributed Makefile's check target explicitly reports that no self tests
are included. Do not count that command as coverage. Native acceptance must
exercise the exact GRUB mformat/mcopy image-file path, recursive EFI directory
copy and byte-for-byte readback, plus supported long/UTF-8 filenames and an
invalid-image negative case. Use only explicit private regular-file images;
no floppy daemon, physical disk formatting or workstation mount is needed.
Then require actual grub-mkrescue assembly and UEFI boot. Source freezing does
not satisfy any of these runtime acceptance gates or change H07's package count.


The inspected manual source contains the GFDL grant but the referenced full
license appendix was not located. Retain the official full 1.3 text alongside
its grant when building the native package. www.gnu.org was unreachable for
this download; the same GNU-hosted text was retrieved successfully from
https://ftp.gnu.org/gnu/Licenses/fdl-1.3.txt and retained unchanged in
LICENSES/GFDL-1.3.txt, SHA-256
110535522396708cea37c72a802c5e7e81391139f5f7985631c93ef242b206a4.
Source-notice inventory now covers 156 frozen archive/patch inputs and 891
named notice candidates, inventory SHA-256
d494accd6d3f4169f280b2c3af79b1500bd337d3ddedafb8cceeb9ed50ef2ab9.
Per-file/manual grants and this additional full license text remain explicitly
identified; the candidate count is not a claim of exhaustive legal coverage.


Prepared H11 recipe follows the archive's configure/Makefile DESTDIR interface,
with --disable-floppyd --without-x. No floppy server/service is required by
regular-file image assembly. Retain the compiled tools, upstream helpers,
man/info documentation, source manual and full GPL/GFDL notices. Declare the
base helper providers; the upstream uz/lz optional lzip-format branch remains
explicitly dependent on a separately installed lzip tool, outside the GRUB
image path and not claimed tested.

The prepared native postcheck generates an actual GRUB x86_64 EFI image,
uses the exact frozen grub-mkrescue mformat geometry/FAT-length and recursive
mcopy invocation, compares retrieved bytes, verifies EFI format, exercises
long UTF-8 names and requires prompt non-crashing invalid-image refusal.
This postcheck has not run; neither a mock nor Makefile's empty check target
is accepted as runtime coverage. Native installation requires H10 completed,
H11 in_progress and the real H09 bootloader success marker. Running the exact
gate through guest Python stdin refused current premature execution (exit 1).
Raw .local/logs/h11-mtools-premature-gate-refusal.json SHA-256
5fffd40a6cc2899f083de34df105b994bb66219396b7d9ca16c5aa3fd3ba5c14.
Shell syntax/Python parsing and 97 local checks pass. No build, installation,
FAT roundtrip or boot is claimed by this preparation.

Subsequent actual preparation and decision: ADR-0078 privately built this exact
Mtools version and passed native FAT behavior plus four real loader-only boots.
The measured grub-mkrescue Apple font dependency led to explicit source-backed
x86_64 BIOS/EFI composition. Production installation and full Linux ISO boot
remain pending; the historical prepared checks above are not release acceptance.

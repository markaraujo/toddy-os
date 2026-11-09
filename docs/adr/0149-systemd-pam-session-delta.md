# ADR-0149: Add PAM to the frozen Systemd session runtime

- Date: 2026-11-09
- Status: Accepted native core, installed runtime and cold-boot/session recovery profile

The accepted261.2 runtime reports -PAM. Its original
src/core/load-fragment-gperf.gperf.in174–178 explicitly maps PAMName to an
unsupported-configuration warning when HAVE_PAM=0. Shipping pam_systemd alone
cannot establish an authenticated Systemd user-session contract. BLFS13.1
recommends enabling PAM on this same version; frozen general/systemd.html SHA256
5543f43390b1e43d99fa6c6c07adede218ec41d112719b8626590ee43fa6dbb1.
This is a concrete B02 dependency, not a foundation restart or version change.

Reuse the existing authenticated source through a private read-only bind input.
All7193regular source files match the frozen archive; the sole changed file is
the already accepted udev group substitution, reproduced exactly from the
original bytes. Preserve the source, old build, accepted archive and G1 evidence.
A new2GiB regular-file compiler volume on builderroot avoids duplicating124MB
of input onto the nearly reserved target. Restore only the recorded image UUID/
inode and the same authenticated source bind after inspecting real mounts.

Build only PID1, executor, their two private libraries, pam_systemd, the generated
systemd-user policy and six directly affected original unit drivers. Pin optional
features to the accepted profile: actual generated HAVE/ENABLE comparison has
exactly one difference, HAVE_PAM0→1. Use Meson's own authenticated install metadata
and depfixer for the five staged ELF files; no build/source RUNPATH may remain.
The compiler cannot write the installed runtime.

The first build compiled all selected targets, with four original drivers OK and
two exact cgroup-v2 prerequisite skips77 (test-load-fragment/test-unit-serialize).
An overstrict own result-name/skip gate ended the job1 before staging. Preserve
that exit1; a stage-only follow-up reused all results/binaries, keeping12selected
artifacts unchanged and actual staged version/module loading0. Neither skipped
driver is a pass: run those two on the native Toddy kernel/cgroups before promotion.

Before a controlled update compare the private exported symbols and payload
against the accepted package; keep every unrelated payload file unchanged.
The reviewed update may replace only the four runtime files and add the PAM
module/policy with exact source/legal provenance. Use a new package revision,
full-root transaction verification, retained predecessor archive and explicit
recovery. Native cold boot, PAMName allow/deny, logind/user-session and recovery
checks are mandatory before accepting the updated runtime. Do not count the
source/loader gate as login, GNOME, physical hardware or B02 acceptance.

The two original drivers subsequently passed on native7.1.8/cgroupv2, with
65+1observed test headers and no skip diagnostics;7193source files and12fixture
files unchanged. Report SHA256df35f12211481740cc9721553e666ff3bb7cf35221bc4a3685b7d99b1002dd13.
Private ELF comparison preserved1112core and6205shared exports, including type,
binding, visibility and object sizes; exactly33PAM-related shared exports were
added. This is an exported-surface check, not complete semantic ABI proof.

Controlled Systemd261.2-1+toddy3 installation passed recipe/post0/0,12root path
changes. Exactly four runtime files replaced; module/policy plus two shared
directories added;2478existing package entries unchanged. The full2486entry
archive payload was compared BEFORE installation; full installed payload, five
CLI consumers, module load and Dpkg/APT checks passed. The predecessor archive
remains available. Native cold boot/PAMName/session/recovery remains pending,
with a separate no-password ephemeral-user fixture prepared. See
[installation](../evidence/B02-systemd-pam-install.json) and
[original native drivers](../evidence/B02-systemd-pam-native-1.json).

The separate updated-PID1 cold boot passed four actual policy/lifecycle cases:
PAMName allow, denial with executor status224, Stop/cgroup cleanup and subsequent
execution as the selected user. Two actual PAM/logind sessions each had active
user manager/default target and a private user D-Bus; close/terminate removed the
session/runtime. Recovery obtained a different real bus identity. No password or
token was needed for these root-requested service/session tests; earlier actual
yescrypt/helper tests remain separate evidence. Eight installed artifacts and the
client were unchanged; temporary account removed, child stopped0/OOMfalse, source
parent unchanged before restart. Report SHA256
f880d12c0f5e4a020e659c1d72b3535290e96f98f82583ed43668b244a8d424f.
See [native session proof](../evidence/B02-systemd-session-native-1.json).

After that acceptance, only the new archive-identical full-package promotion
replica was retired:82108416Breclaimed, full installed root snapshot changed0.
Original compiler stage/source/raw tests and both native archives remain. The
first LLVM-specific root-directory guard refused before any retirement; the
corrected exact Systemd usr/etc/var/DEBIAN check preserves the generic guard.
[Custody/recovery](../evidence/B02-systemd-pam-stage-custody.json) is complete
and must not replay. No GDM/GNOME/physical/B02 acceptance follows from this slice.

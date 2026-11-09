# ADR-0149: Add PAM to the frozen Systemd session runtime

- Date: 2026-11-09
- Status: Source delta staged; native gates and installation pending

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

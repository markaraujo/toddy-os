# ADR-0239: Build the release candidate over immutable accepted B02 disks

Status: source preparation; candidate creation pending
Date: 2026-11-16
Scope: Phase 2 build isolation and recovery; no acceptance

The accepted B02 cold builder/target identities underpin current native evidence.
The next Qt/package/composed-image work must not invalidate those inputs or
silently turn them into the candidate. The foundation/H13 masters stay unchanged.

`scripts/host/phase2_candidate_vm.py` prepares two new writable overlays in
`.local/vm/phase2-candidate`, backed by the accepted B02 images mounted read-only.
Preparation requires the recorded owner authorization, clean source, native boot
lock, no running project VM, exact accepted base identities, read-only QEMU checks
and whole-file base hashes. Existing or partial candidates require inspection;
the tool never repeats preparation over them. No old controller/job is replayed.

The existing builder environment and guarded `/mnt/lfs` target contract remain.
Only the new candidate overlays are writable. A separate fully allocated16GiB
raw work volume uses fixed virtio serial `TODDY-QT-RASTER-1` (below20bytes) and
the proposed `/mnt/toddy-qt-raster-1` mount. Preparation creates no filesystem.
The coordinator must resolve the actual guest serial/device/type/size/mount
ownership before any explicitly guarded filesystem action. Host physical disks
are never candidates. Preserve100GiB+512MiB host reserve and16GiB target reserve.

Prepare/start are excluded while the ADR0237 cold-custody operation holds its
lock. The builder uses the existing12vCPU/12GiB managed VM budget and root SSH
seed on localhost2223; no model/provider credential or publishing key is copied.
The separate candidate name prevents confusing it with the accepted builder.
Source sync, target cache custody, Qt/voice builds and package transactions still
need their own exact inputs, logs, staging/native postconditions and recovery.
The adapter does not run any of them automatically or attach uncertain old work
volumes. SSH operations must follow actual inspected guest/job state.

Stop verifies QEMU exit and unchanged accepted backings, retaining candidate
disk identities. A later installed-image test must boot the actual candidate;
old source-stage disposable tests do not qualify its final packages/image.
No candidate, package, boot or release has been accepted by this decision.

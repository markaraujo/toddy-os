# Phase 2 continuation card

- Authority: [ADR-0113](adr/0113-owner-authorizes-phase2-implementation.md); isolated B01–B13/G2 implementation authorized. Physical testing pending.
- Current: B01 / B01-A clone inventory passed; B01 acceptance still pending.
- Evidence: [B01](evidence/B01.md), [native inventory](evidence/B01-foundation-inventory.json), [cold clone receipt](evidence/B01-foundation-clone.json).
- Actual target: toddy-phase2 KVM builder, separate writable qcow2 overlays over read-only post-H13 cold disks. 12 vCPU/12 GiB; /dev/vdb4 mounted at /mnt/lfs passed guards. No recipe writer active at inventory.
- Last verified: Dpkg audit empty, apt-get check exit 0; unchanged runner scan 18.714 s. GLib and Node absent; accepted dependencies reusable.
- Jobs/logs: VM running; no compile/install job. Local ignored .local/phase2/runtime.json and failure ledger hold volatile details. Inspect actual container/markers/lock before continuing.
- Change/check: next B01-B qualifies isolated unprivileged staging and denied writes. No foundation suite invalidated. Unqualified installs keep full-root checks (ADR-0110).
- Undo: clean shutdown of toddy-phase2, preserve overlays/evidence; cold foundation and released ISO remain unchanged. Never replay prepare over existing state.
- Next: qualify build namespace with a harmless native staging/write-denial fixture, then pin/download native GLib/PyGObject/Node inputs for minimal spikes. Reuse runtime/engine npm lock preparation; no Pi execution yet.

# Phase 2 continuation card

- Authority: [ADR-0113](adr/0113-owner-authorizes-phase2-implementation.md); isolated B01–B13/G2 implementation authorized. Physical testing pending.
- Current: B01 / B01-B native compile namespace passed; GLib bootstrap compile/stage + 14 focused tests passed; B01 acceptance pending.
- Evidence: [B01](evidence/B01.md), [native inventory](evidence/B01-foundation-inventory.json), [cold clone receipt](evidence/B01-foundation-clone.json).
- Actual target: toddy-phase2 KVM builder, separate writable qcow2 overlays over read-only post-H13 cold disks. 12 vCPU/12 GiB; /dev/vdb4 mounted at /mnt/lfs passed guards. No recipe writer active at inventory.
- Last verified: Dpkg audit empty, apt-get check exit 0; unchanged runner scan 18.714 s. GLib and Node absent; accepted dependencies reusable.
- Jobs/logs: VM running; no current compile/test writer; GLib bootstrap-1 exited zero, 14 focused tests passed. Inspect actual process/lock before the package transaction. Local ignored .local/phase2/runtime.json and failure ledger hold volatile details. Inspect actual container/markers/lock before continuing.
- Change/check: next B01-B qualifies isolated unprivileged staging and denied writes. No foundation suite invalidated. Unqualified installs keep full-root checks (ADR-0110).
- Undo: clean shutdown of toddy-phase2, preserve overlays/evidence; cold foundation and released ISO remain unchanged. Never replay prepare over existing state.
- Next: python3 scripts/host/phase2_sync.py --metadata-only, then run_step.py b01-glib-bootstrap-install phase2/glib-install.sh phase2/glib-check.sh --user root inside the Phase 2 clone. Check actual marker/postconditions before any replay. Native GLib 2.88.3/introspection 1.86.0/PyGObject 3.56.3/Node 24.19.0 source hashes are pinned to official SHA-256 files. No Pi execution yet.

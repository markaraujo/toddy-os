# Phase 2 continuation card

- Authority: [ADR-0113](adr/0113-owner-authorizes-phase2-implementation.md); isolated B01–B13/G2 delivery authorized. Physical testing pending; no subagents/model switching.
- Current: B01 / verified native no-write probe; final architecture/root/budget freeze; B01/G2 pending.
- Evidence: [B01](evidence/B01.md), [Node reconciliation](evidence/B01-node-native.json), [native Pi](evidence/B01-pi-native-fixture.json), [descriptor/lock proof](evidence/B01-build-isolation-fd.json).
- Target: toddy-phase2 KVM builder; writable overlays over read-only post-H13 disks. 12 vCPU/12 GiB, guarded /dev/vdb4 at /mnt/lfs; original foundation unchanged.
- Verified: GLib native transaction + 14 tests; Node compile/install committed, initial missing-procfs postcheck failed then unchanged postcheck passed 0/0 with zero payload changes. No reinstall. Native Pi 11 cases/JS framing passed; UID 101, no network. Corrected sandbox closes inherited lock FD; parent lock proof passed.
- Prior jobs: Node build/handoff terminal; handoff command exit 1 is preserved (initial postcheck), resolved by b01-node-native-context.success.json. Never replay b01-node-bootstrap-install. Native Pi fixture terminal 0. QtBase job3 compile/stage0 and b01-qtbase-probe-package recipe/post0/0 verified. First install-preparation failure changed0, no native replay.
- Inputs/logs: .local/phase2/runtime.json/failures.json and actual guest build markers are authoritative for volatile identity. Original harness receipts are not new-harness optimized cache proof; native package transactions keep full-root verification.
- Recovery: preserve overlays, source/stage/cache and failed logs; inspect actual markers/locks before any operation. Never infer success from PID disappearance or silence.
- Next: native Calamares job4 exited0; typed JSON, real Python JobResult, nine negative cases and CLI version passed. Preserve earlier failures. No guest writer currently active. Finalize B01 source/root/license/budget/interface contracts against this evidence, then assess every B01 criterion before selecting B02/B03/B04. Source downloads are host cache only; .local/phase2/runtime.json records jobs.
- Remaining B01: finalized dependency/root/ABI and budget contracts. Model inference, native graphical session, installed image/privilege/recovery and physical validation remain later scoped proof.

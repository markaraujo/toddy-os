# Phase 2 continuation card

- Authority: [ADR-0113](adr/0113-owner-authorizes-phase2-implementation.md); isolated B01–B13/G2 delivery authorized. Physical testing pending; no subagents/model switching.
- Current: B01 / GLib core metadata transaction b01-glib-introspection-install; inspect its actual marker/log. B01/G2 pending.
- Evidence: [B01](evidence/B01.md), [Node reconciliation](evidence/B01-node-native.json), [native Pi](evidence/B01-pi-native-fixture.json), [descriptor/lock proof](evidence/B01-build-isolation-fd.json).
- Target: toddy-phase2 KVM builder; writable overlays over read-only post-H13 disks. 12 vCPU/12 GiB, guarded /dev/vdb4 at /mnt/lfs; original foundation unchanged.
- Verified: GLib native transaction + 14 tests; Node compile/install committed, initial missing-procfs postcheck failed then unchanged postcheck passed 0/0 with zero payload changes. No reinstall. Native Pi 11 cases/JS framing passed; UID 101, no network. Corrected sandbox closes inherited lock FD; parent lock proof passed.
- Prior jobs: Node build/handoff terminal; handoff command exit 1 is preserved (initial postcheck), resolved by b01-node-native-context.success.json. Never replay b01-node-bootstrap-install. Native Pi fixture terminal 0. No guest writer active at this card update.
- Inputs/logs: .local/phase2/runtime.json/failures.json and actual guest build markers are authoritative for volatile identity. Original harness receipts are not new-harness optimized cache proof; native package transactions keep full-root verification.
- Recovery: preserve overlays, source/stage/cache and failed logs; inspect actual markers/locks before any operation. Never infer success from PID disappearance or silence.
- Next: inspect b01-glib-introspection-install.{running,failed,success}.json and .local/phase2/glib-gir-install-1.log. GI scanner is already installed and its corrected private-module postcheck passed; never reinstall it to repeat a check. GLib GIR generation passed with byte-identical core libraries (14 checks reused). After successful metadata transaction, prepare/build PyGObject3.56.3 using pygobject-build.sh, then the native private-bus bridge fixture.
- Remaining B01: native GIO bridge, minimal Calamares/Python/Qt no-write probe, finalized dependency/root/ABI and budget contracts. Model/Qt sources are cached/pinned candidates, not qualified runtime features.

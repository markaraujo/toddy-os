# Fixed MVP candidate-root custody

This source extension uses the existing opaque custody mechanism, without an
arbitrary path/profile option. No guest retirement has been executed by this
source change. It does not establish boot, installer or G2 acceptance.

After reviewing actual inputs and operation postconditions, the sole coordinator
may run the corresponding fixed unprivileged host entry:

```sh
python3 scripts/host/phase2_mvp_offline_candidate_root_custody.py
python3 scripts/host/phase2_mvp_live_candidate_root_custody.py
```

These are separate operations, not an instruction to run both without reviewing
the first result. Offline selects only `toddy-mvp-offline-image-1/root` after
actual matching `toddy-mvp-offline-image-2/mvp-offline-root-2` finalizer reports.
Live selects only `toddy-mvp-live-image-3/root`, before live generation2 exists,
after completed actual resource qualification and independently reviewed protected
`toddy-mvp-live-native-inputs`. Existing standard offline/live slots are unchanged.
The reviewed input reader enforces the corresponding MVP delivery class.

Offline uses `.local/phase2/mvp-offline-candidate-root-custody-1` and
`mvp-offline-candidate1-root.tar.gz`; live uses
`.local/phase2/mvp-live-candidate-root-custody-3` and
`mvp-live-candidate3-root.tar.gz`. Preserve all
intents, partial exports and failures; no replay or overwrite mode exists. Inspect
an uncertain state before any further operation.

The guest route remains the protected image namespace with the already-held
exclusive global FD9 lease and bounded FD8 receipt input. Full raw tar metadata,
PAX/ACL/xattr/hardlink/content proof, complete compressed-stream readback, source
identity recheck, no consumer/mount checks, durable private host copy, actual free
space admission and evidence preservation remain required before exact root-only
removal. It neither removes journals nor adopts candidate1 as generation2. See
[offline custody](offline-candidate-root-custody.md) and
[live custody](live-candidate-root-custody.md) for recovery and proof details.

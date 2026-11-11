# ADR-0220: Qualified private devices and bounded LocalSearch bus reopening

Status: accepted
Date: 2026-11-11
Scope: B02 test infrastructure, not runtime security relaxation

## Observed cause and preserved budgets

Native LocalSearch attempts1–3 remain failed and parked with two unsuccessful
corrections. Exact-path bus qualification SDK2–4 also remains historically failed:
transport substitution, chroot cwd and then an unbooted-target `/dev/null`
placeholder. No successful search or extractor result is inferred from them.
The earlier independent isolated bus-address proof remains valid in its own
profile only. No source, compiler, accepted test or stage is rebuilt.

Actual inspection on the restored builder found `/mnt/lfs/dev/null` to be a
root-owned0644 regular file; zero/random/urandom are absent. These are not the
character devices present after a native boot. Changing global permissions or
creating global target device nodes would conceal the test-profile defect.

## Independent qualification

`qualify_target_private_devices.py` used a private mount/PID/network/IPC namespace,
a read-only target root and a small private `/dev` tmpfs. It bound only the real
null/zero/random/urandom devices, provided fd symlinks and mounted private proc.
Actual owned target Python ran as UID/GID101 with NNP and zero effective/permitted
capabilities. Character major/minor identities, null write/read, zero/RNG reads,
read-only-root refusal and external-network refusal passed. Original global
placeholder/absent-device identities were unchanged after namespace exit.

The first preflight incorrectly assumed all placeholder paths existed. It failed
before receipt creation or namespace dispatch. The correction records actual
absence; no device, permission or package was changed.

## One bounded exact-path reopening

This independent profile satisfies the recorded concrete unblock condition.
Authorize exactly one new SDK5 qualification, preserving all earlier budgets.
It uses the same four private device bindings, original unchanged LocalSearch
3.11.1 helper/config, original read-only compiled cwd and the existing test-only
D-Bus wrapper. That wrapper uses D-Bus1.16.2's supported `--address` override to
select an owned private per-test runtime directory; original policy is retained.

SDK5 passed two real GIO connect/ping/name-query/own-daemon-cleanup cycles in the
exact `/sources/phase2/work/localsearch-1/compile` cwd. All770source/403compiled/
133stage regular-file maps remained unchanged, as did original global devices.
This is target userspace on the builder kernel, not native LocalSearch acceptance.
The prior guest producer was retained rather than overwritten; the new producer
is `qualify_localsearch_private_bus_devices.py`.

## Next bounded native slice

Permit one fresh native attempt4 with the qualified private wrapper/runtime
address in each original test environment. Keep source and compiled trees
read-only and redirect only generated TEST_ROOT to private ext4 as before.
Require both independent qualification receipts and the unchanged frozen
source/build/stage maps before dispatch. Do not repeat the13accepted portable
programs. Require the selected nine original functional/denial programs and
20actual expected cases; preserve any failure and stop this extension if it fails.
Do not remove Landlock/seccomp or substitute mocked search results.

Use the proven dedicated second virtual UART for the unchanged chunk/SHA report
protocol, so kernel/getty output cannot contaminate test evidence. This transport
change does not turn a timeout or incomplete report into success. Cache custody,
current resource reserves and a single guest writer remain prerequisites.

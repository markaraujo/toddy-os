# Native Toddy runtime source

Phase 2 implementation is authorized by ADR-0113. This directory currently contains
the native-qualified B01 Pi1.5 worker/framing/session-D-Bus contract and B03
provider/local/acquisition components. B04 adds a separately tested root executor
and ordinary tools. This is not yet an installed integrated assistant, canonical
task service, GTK UI or G2 release; see each evidence file for exact native scope.

The exact engine npm closure is in engine/package-lock.json. Lifecycle scripts
are disabled when acquiring it; no model, credentials or root grant is supplied.
Host fixture evidence is separately labeled and cannot substitute for native
execution. The native Node source build and later native spike are recorded in
docs/evidence/B01.md and the Phase 2 continuation card.

Worker framing is a four-byte big-endian length and strict UTF-8 JSON, at most
1 MiB. Duplicate keys, unsafe/nonfinite numbers, invalid Unicode, depth >64,
unknown fields/versions, wrong run/tool IDs and truncated frames fail closed.
Sequence numbers in JSON are bounded to 2^53-1 for exact JavaScript/Python
interchange. D-Bus task sequences remain uint64; a JSON-facing sequence must not
silently exceed that safe-number bound. Opaque IDs remain bounded strings.

The fixture has one active run, one pending tool and sequential Pi execution.
Tool requests return through the broker-facing pipe; no worker filesystem/root
tool executes. EOF aborts the run; cancel aborts a pending tool. A worker done
event is not verified canonical task success or a promise to reverse effects.
The broker/executor will own durable request/operation reconciliation in B04/B05.

The D-Bus contract includes bounded config validation plus FD-based profile bundle
staging/export. B01's native GIO probe must verify it before final freeze. The
broker must authenticate the actual sender, accept only bounded regular input
FDs, copy and validate actual bytes into private staging, bind staged revisions
to the sender for at most ten minutes, and revalidate on compare-and-swap apply.
It never accepts privileged paths/grants from imported content. Exports omit
connection references and credentials; native implementation belongs to B06.

Offline base setup remains independent of these engine/backend files; acquisition
of the assistant later must not require OS reinstallation.

## B03 optional backend setup

The provider factory and private local runtime now have native evidence under
B03. Remote adapters are protocol-fixture-only/live-unverified. No default remote
spend, fallback, model download or activation. `runtime/acquisition/cli.py plan
--mode deferred` returns offline-base availability. API planning accepts adapter,
model ID and connection reference; never pass a credential on its command line.

For local acquisition create an owned0700 cache, inspect `plan --mode local
--cache /absolute/cache`, read the pinned license and approve the network/size.
`download --mode local --cache /absolute/cache --approve-network
--approve-license Apache-2.0 --artifact-sha256 <displayed-sha>` acquires only the
trusted catalog artifact. SIGINT/SIGTERM preserves private partial bytes; repeat
the explicit command to resume after inspecting the result. Verified cache reuse
rehashes bytes. Integrity/conflict errors require explicit inspect/remove; no
failed artifact activates. The library/API is reused by later native settings.

B04 user file/shell tools run without root, scope file methods to an owned workspace
and bound process/output/Stop behavior. Arbitrary shell has normal account powers,
not plugin confinement. The independent executor has no grant mutation in its
broker-facing API. Deliberate root policy client grants/revokes until the owner
polkit surface is qualified. Active root Stop/revocation/service-loss recovery are
native-tested; installed cgroup and package/service/network paths remain pending.

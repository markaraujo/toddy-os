# ADR-0117: Private local runtime and bounded provider lifecycle

- Date: 2026-11-07 America/Sao_Paulo
- Status: Accepted native B03 local slice; external provider/acquisition proof pending
- Scope: Existing llama.cpp/Pi architecture, no new framework/provider dependency

Pinned llama.cpp0.9.0 supports Unix paths ending in .sock through its --host
option ([exact source](https://github.com/ggml-org/llama.cpp/blob/cd959bae99ff4bed22bef2604f45241c09bbb8c8/tools/server/README.md)).
Use an owned child process and socket in a fresh0700 user runtime directory,
plus a random0600 bearer file. The Node adapter implements HTTP semantics over
that socket, with a fixed placeholder origin and no DNS/TCP/redirect route.
This fits B01's private local-process fallback and avoids a public listener or
port-allocation race. No profile import supplies a raw socket path or credential.
The broker resolves its private connection reference; credentials do not enter
model messages, command arguments, diagnostics or exports.

The runtime refuses root execution, checks the CPU profile/available memory,
verifies actual model length/SHA256, and passes a read-only model FD to the
sanitized child environment. GPU, downloads, hosted fallback and model-server
subprocess tools are disabled. Administrative tools remain the independent
executor's responsibility, not an elevated model process. Stop reconciles the
owned child, reports forced termination honestly, removes private state and is
idempotent. Session/logout integration and durable operations remain B05/B06.

[Native local-tool-8](../evidence/B03-native-local-tool.json) passed an actual
Pi-agent disposable-file read/answer, otherUID65534 socket/key EACCES, bearer401/401,
active generation cancellation6ms and a successful new request, exact local
context rejection before generation, and graceful/idempotent model Stop. Source
hashes and the input contract snapshot bind the measured scope. The current
profile uses explicit temperature0 and a bounded short file marker; earlier
stochastic/formatting/provider failures remain. This is not a universal model
accuracy or physical/reference-machine performance claim.

Each provider instance belongs to one pinned task, including its tool turns.
Import only the selected Pi protocol module; disable retries and implicit remote
fallback. Keep per-request leases so completed-stream cleanup cannot clear a
followup's ownership, and do not abort a successfully completed HTTP stream.
Bound request/response/output/queue sizes and return classified failures instead
of raw SDK errors. Remote dispatch requires explicit task consent, enabled request
budget, resolved credential and selected model; price remains unknown without a
verified pricing input, never an advertised hard billing cap. External live calls
are untested until explicitly supplied/authorized; fixture proof is separate.

For the selected local profile, authenticate /apply-template and /tokenize calls
before generation. The pinned server uses the same chat/tool parser for template
application and actual chat generation. Count those real tokens and reserve the
output budget; reject context overflow without silently trimming/retrying or
starting inference. Remote adapters expose configured catalog limits/provider
errors; do not claim an exact remote input tokenizer or hard monetary cap from
the local proof. Remaining protocol fixtures must describe that distinction.

An explicit developer-fixture observer may retain bounded **synthetic-only**
failure diagnostics with the actual ephemeral key removed. Default runtime
diagnostics remain classified and exclude payloads/credentials. This code hook
is not a profile/SKILL.md hook or authorization input.

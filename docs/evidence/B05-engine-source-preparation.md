# B05/B06 production engine transport source preparation

Source-only production transport plus actual host process/protocol checks. No
actual model inference, paid provider qualification, installed target/broker/UI,
credential setup or B05/B06/G2 acceptance is claimed by this slice. B03's existing
real local-model evidence remains distinct from these tests.

`runtime/engine/worker.mjs` uses the pinned Pi1.5 Agent and the existing actual
createProvider factory by default. The CLI accepts no replacement provider hook.
Module-level tests can inject a deterministic factory explicitly; the original
B01 fixture-worker and its frozen protocol remain unchanged.

Bootstrap profile, canonical revision, connection, model catalog, persona and
installed tool schemas arrive only through an owned bounded private FD. The broker
adapter creates an actual0600 sealed Linux memfd; credentials never enter argv,
environment values, tool/model context, status or logs. Environment contains only
fixed runtime values and the numeric FD. The selected provider receives its
credential through the existing private provider boundary. The worker cannot
perform native tools or change grants; every actual effect returns to trusted
broker code through framed tool requests.

Hello negotiates agent-runtime-v1/runtime-tool-result-v1/single-run/cancel while
retaining strict version1 framing. New runtime tool_result carries explicit
verified/rejected/uncertain outcomes; uncertainty aborts the loop and forbids more
tools. One task is bound to the private bootstrap revision. Envelopes/sequence/
run/tool IDs, frame/argument/text/tool/request limits,32 pending output writes,
write readiness, deadlines, Stop and EOF are enforced independently. A worker done
event is never canonical effect proof. The adapter requires a clean worker exit.

An initial synthetic cancellation regression exposed that aborting Pi alone can
leave a synchronous provider repeatedly requesting tools. Source correction uses
Pi1.5's finishTurn hook, an independent request budget and an event-loop yield
before every provider turn, preserving timers/Stop even for hostile fast output.
The corrected Stop/uncertain/deadline/budget tests all pass. This does not modify
Pi or relax provider limits. A separate unavailable-executable fixture initially
expected direct Popen failure; the fresh parent-death launcher correctly failed
later at exec, so the expected fixed engine_disconnected classification was fixed.

`runtime/broker/engine.py` launches the worker through the existing fresh
parent-death helper, avoiding threaded preexec_fn. It scrubs environment, drains
and discards bounded raw stderr, reads incrementally without losing partial frames
on cancellation polls, validates negotiated envelopes and returns only fixed
classifications plus private text callbacks. The caller owns canonical journaling,
consent, credentials and trusted verification. The engine process has no native
effect to kill; independent package/executor writes retain their safe boundaries.

Focused results on the development host:

- `node --test --test-reporter=spec --test-timeout=6000 runtime/engine/worker.test.mjs`:
  eight checks,1.109seconds; real pinned Pi loop with test-only synthetic provider,
  actual framing/tool roundtrip/text, Stop/uncertainty/deadline/EOF/request limits,
  invalid IDs/revisions and classified raw errors.
- `python3 -m unittest discover -s tests -p test_engine_adapter.py -v`:
  five checks,0.326seconds; actual owned sealed memfd, child text/Stop, envelope/tool
  refusal, missing executable and raw-stderr privacy. These process fixtures use
  synthetic workers and do not qualify a provider.
- `/usr/bin/python3 tests/fixtures/engine-runtime/smoke.py`:
  actual production worker/default createProvider/Pi and private Unix HTTP synthetic
  protocol passed in0.170seconds. One actual temporary fsynced file effect returned
  through the broker callback, two generation requests, actual streamed text,
  credential absent from model body/output, clean completed worker. The Unix HTTP
  response is synthetic; this is explicitly not model/inference acceptance.

Node dependencies were read from the already audited local Pi closure through an
ignored temporary linkage; npm acquisition/lifecycle scripts were not run and the
closure was not modified. Native qualified24.19 testing and actual accepted local
model remain the coordinator's next qualification, followed by durable broker
conversation/text/settings APIs and protected setup. No history or root-policy
store is created by the worker.

Repository `make check` passed416checks in7.114seconds for this source slice.

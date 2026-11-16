# B05 durable task source preparation

Source-only B05/S08-S10 preparation. No installed broker, native target task,
configuration restoration, story acceptance or release gate is claimed here.

`runtime/broker/tasks.py` extends the same canonical per-profile `state.sqlite`
used by profile revisions. Acceptance atomically stores request/input hashes,
profile pin, deadline, bounded tool count and minimal lifecycle metadata; no
prompt/tool arguments/results or arbitrary exception text is stored. Repeating
the same request returns its task; changed input, metadata or revision conflicts.
A separate authenticated user-session service must bind peers and validate tools.

One file lock serializes dispatch and startup recovery. An operation is durable
before effect dispatch. Unexpected failure or absent verified postcondition holds
uncertainty; repeated operations never apply an effect again. Startup holds all
unfinished work for review. A trusted read-only inspector can prove a known effect,
otherwise it stays uncertain. A recovered prepared operation also requires review
and cannot run merely because a client repeats the request.

Stop cancels queued work and blocks new dispatch. In-flight package/boot work
reports its active operation/safe-boundary wait instead of killing an unknown
writer. The adapter observes cancellation for interruptible work; after a known
verified effect the task records stopped-after-effect. Stop never hides an
uncertain effect behind a canceled/successful terminal result. Current executor
policy/revocation remains independent and must be rechecked by the root service.

Capacity preflight includes DB/journal/WAL files and additional dispatch headroom;
64 MiB default journal limit plus a 2 MiB disk reserve refuse new work before
effects. Commit errors still fail dispatch; reserve is no guarantee against
concurrent disk exhaustion. No active/uncertain record is deleted. Terminal
30-day pruning/tombstones and runtime monotonic adapter deadlines remain service
integration work; this slice never silently expires/replays an old request.

Focused command: `python3 -m unittest discover -s tests -p test_task_journal.py -v`.
Eight actual host SQLite tests cover crash after fsynced effect/before result,
read-only reconciliation without replay, request binding after profile change,
Stop before work and during a concurrent package safe-boundary wait, missing
postconditions and secret exception refusal, bounded storage/deadline/tool count,
and recovery of queued/prepared operations. The initial focused run exposed a
test-clock mismatch (fixture used a real clock against a synthetic deadline);
correcting the fixture clock preserved the deadline implementation. Additional
review added a regression that recovered prepared work cannot dispatch from its
waiting state. Native integrated S08-S10/S24-A remain pending.

Repository validation: `make check` passed 405 checks in 6.184 seconds after the
prepared-operation recovery refusal regression was added.

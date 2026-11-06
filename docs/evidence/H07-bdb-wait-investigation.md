# H07 Berkeley DB wait investigation

Observed on 2026-11-06, 21:31–21:33 UTC. The owner requested a concrete check
for a hidden blocker or infinite loop. This is partial execution evidence,
not full Berkeley DB or H07 acceptance.

## Measured progress

| Observation | Current variant's last checkpoint | ALL.OUT bytes |
| --- | --- | --- |
| 21:31:15 UTC | Iteration 59 | 3265315 |
| 21:33:15 UTC | Iteration 104 | 3265409 |

Both observations refer to the same native Tcl process and the same Recd011
btree partition-callback variant, started at 21:29:01. The preceding range-
partition variant had finished its increment loop, recovery at each timestamp,
and before/after timestamp checks. Its recorded duration was 7m10s. Repeated
Recd011 headings here describe distinct finite test variants, not a restarted
build or an automatic retry loop.

The original driver/runner remain alive. Their wait states are waiting for
children; the active Tcl child is in do_select, consistent with its timed
waits. The actual driver invokes run_step.py once. That runner creates one
recipe process and waits for it. The recipe invokes run_std once and requires
the complete success sentinel plus native installation postchecks; it does not
silently retry a failed standard suite.

## Source-backed explanation

The verified source test/tcl/recd011.tcl declares niter=200, ckpt_freq=15 and
sleep_time=1. Its loop is inclusive, i=0 through i=200: 201 iterations. Each
iteration calls tclsleep twice to separate the commit and recovery timestamp.
testutils.tcl implements tclsleep as after(s*1000+56), so the deliberate sleep
budget is 201 * 2 * 1.056 = 424.512 seconds, before recovery and other work.
This is about 7m04.5s and agrees with the previous variant's measured 7m10s.
Checkpoint output occurs only every fifteen iterations, roughly every 31.7s.

test.tcl's partition dispatch deliberately runs range partitioning and a
partition callback over its finite test/method lists. No sleep, assertion or
test variant was removed to shorten this run. This explains the current wait;
it is not an ETA for the entire remaining standard suite.

Source SHA-256:

- recd011.tcl: `4fbf640c84a52079cb6d3dfdd15318688e10c0c10cf255f121c8282d90aab581`
- testutils.tcl: `07f38042356fd444e83708843b87081f4ae1c854d590b0883c00fe5bafd24cd3`
- test.tcl: `81b82f33c9ca4fc878ee51fd1f235645824f1d4faba28d187bc23955c21681df`

## Resource and result boundaries

The guest had approximately 11 GiB available RAM, no swap use and 128 GiB free
on the target filesystem. Memory pressure averages were zero and recent I/O
pressure was low. The host had approximately 12 GiB available RAM and 340 GiB
free on the repository filesystem. No current memory/disk exhaustion explains
this wait. These snapshots are not a promise that future resource pressure or
implementation failures cannot occur.

No FAIL or final Regression Tests Succeeded sentinel appeared in the observed
partial log. The driver has not written its final exit. Production Berkeley DB,
APT and final metadata acceptance markers are still absent. All 124 currently
installed packages report install ok installed. The current evidence supports
an advancing timed test, not a hidden block or infinite loop at this point.
Continue monitoring the same execution and inspect its actual final outcome.

Raw observations outside Git:

- .local/logs/h07-bdb-loop-investigation-first.json, SHA-256
  `2f5b8c334618209a97cd952ad4c2ae3c57e85e66fbfe3c56fa1ba991f654e008`.
- .local/logs/h07-bdb-loop-investigation-second.json, SHA-256
  `a548267eeb446b7d0fbe6ef5aed8739fae5f5f97a253a5b81deecc782737b218`.

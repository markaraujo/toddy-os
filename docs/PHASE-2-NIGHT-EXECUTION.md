# Phase 2 — Unattended execution review and failure simulation

Date: 2026-11-07. Owner requested overnight progress with autonomous routine
technical decisions, bounded diagnosis and economical context use. This is a
planning/tooling review, not guest-start approval, a running overnight session,
a scheduler installation or evidence that runtime failure tests passed.

## Findings that affect delivery speed

1. **Actual selector starvation:** next_eligible preferred a blocked B03 over a
   ready B02. Corrected: preserve an in-progress story, otherwise select ready
   unblocked work; if all eligible work is blocked, report a blocked prerequisite
   rather than bypass dependencies. Regression checks cover both paths.
2. **B01 is the sole graph entry:** its failure stalls all B stories. Split its
   existing work into persisted slices: inventory/resources, dependency lock,
   engine/binding fixture, no-write installer probe, architecture acceptance.
   Timebox each unknown separately. Do not wait for all B01 work to make commits.
3. **B01 proof can accidentally become B02/B12:** build only dependencies needed
   for the pinned minimal probes in a disposable target. No completed GNOME
   desktop, full installer or full model benchmark is required by a fixture.
   Dependency compilation may still be expensive; save reusable packages/evidence.
4. **Active checkpoint can become a retry trap:** before changing branches, record
   cause, attempts, failed input identity, verified checkpoint and exact unblock
   condition. Mark that story blocked, preserve its evidence, then choose eligible
   work. Do not leave an abandoned story in_progress merely to remember it.
5. **Fallback authority was dispersed:** use already selected fallbacks without a
   routine owner question. Ordinary launcher instead of Shell overlay, eSpeak NG
   instead of an incompatible Piper voice/runtime, deferred unsupported optional
   download. Core ABI/engine/installer replacement needs a concrete blocker and
   narrow ADR; not a broad new framework survey or silent feature omission.
6. **Publication can consume the whole run:** push failure must not erase local
   progress or launch repeated auth attempts. Save commits and sanitized error,
   continue authorized local work and retry only after access/network changes.
   Release delivery remains incomplete until publication/portal checks pass.
7. **Night execution depends on a live runtime:** verify host sleep/power/session,
   permissions, target access and available resources before launch. Record limits;
   never promise that chat instructions bypass session/usage limits. Do not change
   global host power/security settings silently to obtain continuous execution.

## Reproducible structural simulation

Run `python3 scripts/simulate_phase2_plan.py`. Read-only stdlib simulation loads
actual status dependencies and exercises the actual next-story selector. It assumes
each visited story succeeds; it does not model build duration or validate a guest.
It injects one blocked story at a time across all 13 B stories and checks nominal
reachability. No approval/state/files are changed by the simulator.

Recorded [structural results](evidence/phase2-dependency-simulation.json) bind the
actual status input hash. Observed graph results on this revision:

| Injected blocker | Work still reachable | Implication |
| --- | --- | --- |
| B01 | No B-story implementation | Resolve bounded B01 slices; independent source/docs prep only, never mark it passed to continue |
| B03 | B02 after B01 | Work on desktop while engine cause is isolated; B04 still cannot start |
| B02 | B03/B04/B05/B07/B08 after B01 | Headless service/memory/scheduler can progress; no invented desktop acceptance |
| B09 | All except B09/B13 | Finish plugin branch; G2 waits for scoped speech proof/fallback |
| B12 | All except B12/B13 | Other eligible features can progress; never label a live-only image installable |

## Failure tabletop and exact next behavior

These are reasoned fault-injection walkthroughs, **not executed runtime tests**.

| Scenario | Decision and next safe action | Avoided loop / owning proof |
| --- | --- | --- |
| Host sudo needs password | Record concrete missing permission; continue source/fixtures, no password prompt loop | Dependency authorization does not create privileges |
| KVM unavailable | Inspect permissions/device once; use supported existing QEMU fallback only with measured budgets, otherwise preserve blocker | No repeated VM provisioning |
| Source URL unavailable | One transient retry; verify approved alternative mirror against same hash | Never upgrade baseline to fix a URL |
| Hash mismatch | Quarantine bytes, inspect provenance/mirror; no extraction or blind repeated fetch | Integrity gate retained |
| Python/Node ABI incompatibility | Small reproducer, inspect pinned upstream support, apply one justified compatible recipe/version decision | No entire base rebuild or framework carousel |
| OOM compiling browser/Qt | Inspect actual memory/log, lower jobs or approved build allocation; reuse completed packages | No unchanged high-parallelism retry |
| Stalled build with live CPU/output | Monitor process/log/progress at bounded intervals; keep one writer | No duplicate compiler job |
| Silent hung process | Diagnose process/resource wait and safe cancellation; checkpoint if needed | Never SIGKILL a package transaction just for a timer |
| Local model too large | Verify measured budget, choose supported reference/fallback via ADR if necessary | No survey/download of many models |
| Provider credentials absent | Use deterministic adapter fixtures; remote integration explicitly untested; local proof still required | No request for keys overnight or false live-provider claim |
| Installer optional app unsupported | Leave option unavailable with reason and proceed with tested base | No blocking entire OS on VS Code packaging |
| Installer/backend fundamental failure | Isolate no-write probe and narrow upstream alternative review; preserve B12 blocker | No improvised destructive installer |
| UI/worker reconnect after crash | Inspect durable operation/postconditions and reattach | Never replay a write because output was lost |
| Full target disk | Measure usage, remove only verified disposable build/cache data; preserve logs/checkpoints and preflight again | No automatic deletion of recovery evidence |
| Session compaction/restart | Read short card, verify actual Git/VM/job identity and changed hashes, continue one next action | No whole-plan reread or duplicate writer |
| Passing test | Save result once and move to next slice | No repeated unchanged suite for confidence |
| Repeated same error | Consult attempt ledger; new evidence/correction required before another attempt | Prevents spending tokens rediscovering the same failure |
| No runnable branch | Save precise blocker summary and stop useful execution cleanly | No idle polling or manufactured progress |

## Attempt and decision budget

For each failure keep a local structured ledger in ignored .local/phase2/: story,
slice, input/recipe hash, normalized error fingerprint, attempts, elapsed diagnosis,
last correction, result and unblock condition. Public evidence contains sanitized
facts only. Same fingerprint/input cannot be treated as a fresh failure after
compaction. A new chat does not reset the attempt budget.

Allow one unchanged retry only for classified transient infrastructure. Otherwise
change a diagnosed cause before rerun. After two unsuccessful corrective attempts
or 30 minutes of active diagnosis of the same cause (whichever comes first),
checkpoint it and choose another eligible branch. This bounds diagnosis, not a
healthy build's execution time. An ongoing safe write must be reconciled before
switching. A new concrete hypothesis with new evidence can justify one logged
budget extension; repeating the same explanation cannot. Do not ask the owner to
choose routine compiler flags, mirror, package layout or selected fallback.

Every intervention must produce a correction, useful observed evidence or a
checkpoint/blocker. After two consecutive interventions producing none, stop
replanning that slice and change to eligible work. Do not spend another cycle on
art/docs merely because guest work is hard. No compulsory token estimate: usage
limits depend on the actual runtime and are not guaranteed by this plan.

## Start, monitor and finish one unattended run

After explicit guest authorization, perform one preflight: accepted source/target
identity, recoverable checkpoint, G1/approval state, noninteractive actual access,
RAM/disk/job budget, verified source/network availability and relevant host sleep/
session limits. Save pending user-only actions once. Start the first eligible
slice; install authorized dependencies and resolve routine choices autonomously.
Do not create a second agent scheduler, broad sudo policy or watchdog with bypass
powers. One guest/package writer; bounded independent read-only prep is allowed.

Prefer process handles, exit status and log deltas to model speculation. Start
monitoring long builds at 60-second intervals, increasing to five minutes while
progress is healthy; the assistant's interactive waits remain at most 60 seconds.
Use deterministic local monitoring for longer intervals if available, not repeated
LLM calls to reread unchanged logs. Store full logs locally and inspect only tails,
new error context and required postconditions. No scheduled LLM invocation merely
for unchanged monitoring. A local monitor cannot create/extend an agent session.

Commit each verified slice. Validate affected checks once, broaden only on changed
inputs/new failure. Keep the current story, real job/checkpoint, last result and
one exact next action on the continuation card. On budget/session/end-of-run,
leave running jobs only with recorded identity/log and safe containment; otherwise
stop at a safe boundary. Report completed commits, actual evidence, remaining
blockers and next action. Never promise completion by morning without measurements.

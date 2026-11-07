# ADR-0110: Isolated package builds and change-based validation

- Date: 2026-11-07 America/Sao_Paulo
- Status: Accepted design; target qualification pending B01/B02
- Scope: Phase 2 build execution and developer validation, not product plugin policy

The owner accepted prevention of out-of-package writes to reduce repeated full-root
hashing, and requested a per-interaction decision about necessary testing. Preserve
SHA-256, existing foundation evidence and essential safety gates. This approval
changes the implementation strategy, not the guest-start boundary of ADR-0063.

## Package integrity strategy

Compile as an unprivileged builder in the designated disposable target. Make
source/dependency inputs read-only and expose only declared writable build and
staging roots. Do not expose host paths, signing material, credentials or a writable
system root. Staging is an output directory, not itself a sandbox. Fail an attempted
out-of-scope write and preserve its diagnostic; do not grant wider access merely
to make a recipe succeed. No global host security changes are implied.

Verify staged regular files, links, paths, permissions, licenses and ownership;
reject escaping links, special files and collisions. Install through the native
package transaction backend with manifest-derived expected changes and before/
after checks of affected resources. Narrow verification includes removals and
replaced files, not only new files. User-conffile preservation stays explicit.

Maintainer scripts, triggers, generated caches, service activation and boot/schema
updates are side effects beyond a staged file list. Declare their exact intended
resources and postconditions and qualify them separately. Do not claim the native
package manager automatically confines root scripts. A transaction that cannot be
confined or completely accounted for retains the existing full-root before/after
verification in a disposable guest; a full hash diff detects changes after they
occur, not prevents them. Preserve recovery and independent policy controls.

Before enabling the optimized path prove: allowed staging writes work; outside
writes are denied; source/dependency mutation is denied; escaping links and
collisions fail; controlled installation accounts for files/removals/side effects;
failed transactions reconcile; temporary outputs cannot become a false cache hit.
Use harmless fixtures first. Measure elapsed scan/compile/install/check costs on
the actual target. Only qualified recipes may replace per-step full snapshots;
unqualified and broad privileged recipes keep the existing path. Full checkpoint
and exact-final-image closure checks remain. Never reuse evidence across changed
sandbox/recipe/dependency/package identities without affected revalidation.

## Every interaction chooses; only affected changes trigger tests

At each work boundary inspect the diff and changed inputs. If no executable,
configuration, artifact or relevant requirement changed and no failure is pending,
reuse the last identified evidence. A conversation/status request is not a test
trigger. A previous pass is reusable only for the same relevant identities.

For changes, identify direct behavior, affected consumers and failure/safety edges;
run the smallest meaningful checks that establish those postconditions. Broaden
when shared interfaces/ABI/policy/storage/boot/package behavior changes, a failure
suggests wider impact, the affected closure is unknown, or a final release gate is
due. Unknown impact requires tracing it, not assuming the smallest test suffices.
Broad means the affected integration set, not automatically every historical suite.

No automatic whole-system rebuild, unchanged compiler/libc tests, full hardware
matrix or repeated soak for a local change. make check remains required for
repository delivery; currently it is cheap and catches cross-document consistency.
Keep mandatory boot/install, privilege/credentials, replay/cancellation and recovery
checks when affected, plus the exact final candidate's combined gate. Owner-use
backlog cannot replace them.

Record changed scope, selected checks, reused evidence identity, result and next
action in the existing slice/evidence card. Do not create another report for every
chat message. Rerun after a fix only the failed and newly affected checks; passing
unchanged results do not need another confidence run. The bounded retry/diagnosis
policy in PHASE-2-NIGHT-EXECUTION.md still applies.

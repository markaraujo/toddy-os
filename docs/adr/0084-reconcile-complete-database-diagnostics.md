# ADR-0084: Reconcile complete database diagnostics before terminal qualification

- Date: 2026-11-07
- Status: Native review components verified; complete corrected result pending
- Extends: ADR-0069, ADR-0079 and ADR-0083

## Decision and boundary

Implement an independent terminal review instead of treating zero FAIL alone as
success or erasing the failed upstream summary. PRD section 5 requires identified,
source-justified expected failures; it does not authorize accepting an incomplete
run. The measured Test142 formatting defect and limited recovery tracker have
specific source/native evidence in ADR-0083. Any later qualification must still
inspect the complete actual run, all assertions, immutable execution inputs,
coverage witness and protected custody before production nomination.

The new components do not accept a package or change either actual exit code.
The existing strict success gate remains strict: zero process exits, complete
upstream success, unchanged verified inputs, protected source/reports, no FAIL
and no unexpected output. The production nomination continues to use that gate.
No qualified-result production branch is introduced by this decision.

## Independent native reconciliation

scripts/build/db_standard_diagnostics.py extracts only check_output from the
hash-pinned frozen test.tcl and runs it with actual native Tcl against a new
private copy of the completed report body. It never sources the dispatcher,
runs database tests, filters the original report or edits its summary. The two
terminal summary lines are outside the original checker input by upstream
design; the original complete report remains unchanged and is hashed.

Reconcile every resulting unexpected-output line with the captured standard.log.
Require its exact original start/version, all 35 outer headers in order (27
groups with nine final access methods), native diagnostics, failed summary,
completion timestamp and strict entry's actual failure line. Missing/repeated
headers, truncated output, new stderr or disagreement between native checker
and report failures prevent review. Classify real FAIL entries independently;
qualified text embedded inside a FAIL never converts it into an informational
message. Diagnostic-only readiness requires exactly thirteen known Test142
lines, one of each ten known coverage warnings and zero real/unknown failures.
It still returns suite_accepted=false and package_accepted=false.

The actual original 12,282,570-byte ALL.OUT was rechecked. Native Tcl reproduced
all 25 unexpected lines; classification found two real failures and no unknown
lines. Diagnostic-only readiness correctly refused that original result. The
still-live corrected summary also failed the completeness check. Native report
SHA-256: e1775d2ec868f2693fdf30d2237dccdd33235ffa8521a90e0de5c869c9fcd616
(.local/logs/h07-db-terminal-diagnostics-<sha256>.json).

Original ALL.OUT SHA-256:
2f75c918ba8d713db23435355e62af25c3b4b623f1c5a802d09d41b1e2ccab7c.
Original standard.log SHA-256:
2d0441963aad69dda37ee0f26fd4814ea35541bec2e5008390eb6a8779c38283.
The copied body SHA-256 is
9f84b57a5494ee9889cce589b5299ebba6e43aacd05121ffc623b6e7cefc8d0f;
independent native checker stdout SHA-256 is
4fa41d2f20f863b994ba38f3eb6da00653e47e985d8276c43fedb8fc4c3c6c88.

## Bind the actual coverage witness

scripts/build/db_coverage_result.py verifies ADR-0083's exact measured terminal
result, root-protected manifest, producer, 0/0 exits, complete sentinel, actual
record counts and namespace/tmpfs evidence. All 10,208 source entries are
rehashed and compared with the complete standard execution's input manifest.
Only the explicitly reviewed diagnostic entry may differ. A live producer,
changed input/report, absent type, different standard pairing or a claim that
the focused experiment itself accepted the full suite is refused.

This is a deliberately specific recovery witness, pinned to the actual observed
result. It is not a generic claim that arbitrary future tests pass or a portable
substitute for fresh native verification. Source custody is not sealed by this
read-only component. Future installation still needs protected source custody.

Actual native witness verification passed, as did sixteen rejection cases:
eleven changed result fields, outside/wrong pairing, the unfinished full review,
the unfinished strict success gate and using focused coverage as a full result.
No complete-review output directory or production nomination was created.
Raw report SHA-256:
6839dcca04bc5db9e13b9a0097ec1724d7f9e3ba4d7d34f55ffe1cc3de3eb0e3
(.local/logs/h07-db-coverage-verification-<sha256>.json).

## Prepared complete review and original history

scripts/build/db_standard_review.py is a separate read-only review path for the
specific full producer's terminal exit-1 profile. It takes the build lock and
requires quiescent dispatch/synchronization. Common execution/input/isolation
checks were factored out of db_standard_result.py without changing the strict
success interface. Failed-source review checks actual bytes but does not claim
root-private custody. The prepared review combines those checks, the bound
coverage witness and independent native summary reconciliation, then rechecks
inputs before recording review.json. Raw exits remain 1, and all suite/package/
custody acceptance flags remain false. Its complete positive invocation awaits
the actual corrected run's termination; no synthetic full result is substituted.

The original-history guard now pins the two exact terminal report hashes above,
in addition to its existing exact recipe/start, exit 1, two known FAIL entries,
complete summary, unchanged recipe log and empty installed-change manifest.
This permits preserving the diagnosed failed attempt in history. It does not
accept that attempt or relax the corrected-result requirement. An actual guest
prepare invocation passed original-history validation and then refused the live
corrected run, without creating a history archive or candidate.

Alternatives rejected: a generic warning allowance loses evidence specificity;
rewriting exits/summary misstates what ran; combining focused passing groups
cannot prove the unfiltered standard suite; duplicating provenance logic risks
weaker recovery checks. Native reconciliation plus shared byte/provenance checks
keeps these obligations explicit. The guarded production qualification and
fresh-build diagnostic handling remain implementation work after complete review.

Reproduce components without syncing or editing active inputs:

```sh
python3 scripts/host/probe_bdb_terminal_diagnostics.py
python3 scripts/host/probe_bdb_coverage_result.py
```

Four local regression methods additionally reject malformed summaries, filtered
output, missing dispatches, unknown warnings, real assertions, changed counts
and fabricated exit/producer states. The local small parser fixtures are tests
of rejection logic, explicitly not native complete-suite evidence.

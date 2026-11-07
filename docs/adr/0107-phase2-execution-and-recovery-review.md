# ADR-0107: Risk-first Phase 2 execution and resumable delivery

- Date: 2026-11-07 America/Sao_Paulo
- Status: Accepted planning refinement; implementation versions remain provisional
- Refines: ADR-0105/0106, B01-B13, development validation and continuation procedure
- Preserves: ADR-0063 approval boundary, all foundation evidence and G2 product scope

The owner requested a complete gap review, better execution/testing and protection
against losing AI context. They emphasized quality and small traceable deliveries,
without withdrawing the earlier focused-basic-test policy. Adopt the findings in
[the review](../PHASE-2-REVIEW.md), the execution playbook and short continuation
card. Do not construe this request as guest-start approval.

Use a risk-first eligible sequence, preserve an active checkpoint, and front-load
UI/engine IPC, installer feasibility and installed-root/package contracts. Split
premature smoke requirements by owning stage. Keep a compact final installed-image
pass with all accepted components; smaller text snapshots do not complete G2.
Enforce existing owner-start and story/status consistency rules in planning tools.

Clarify real plugin confinement versus separate processes/logical profiles, write
serialization/revocation, post-effect crash reconciliation, keyring failure,
installed-image hygiene, migration/deletion, missed schedules and narrow browser
integration. These clarify existing product boundaries rather than introducing
another framework, paid service or mandatory external assistant.

Each working slice records actual inputs, target checkpoint, affected checks,
results, safe undo and one next action. A resume inspects Git and live target/job
state before reusing evidence or replaying an operation. Builds may take time;
bounded monitoring and targeted regression checks replace blind repeated suites.
"Perfect" is a quality objective, not an exception to honest pending evidence.

Alternatives rejected: wait until B12 to discover installer incompatibility;
run every unchanged upstream suite for each slice; trust chat summaries/PIDs;
assume another PID isolates secrets; call an incomplete optional-feature snapshot
G2. All either increase late rework or hide unresolved risk.

Official source observations and versions are listed in the review. Actual
runtime proofs remain B-story acceptance, not this documentation change.

The owner subsequently requested closure of open design decisions before starting.
Adopt [PHASE-2-DESIGN-BASELINE.md](../PHASE-2-DESIGN-BASELINE.md) as the component/IPC/
model/voice/sandbox/browser default selection. OPEN-DECISIONS.md now distinguishes
closed design from unrun implementation proof and remaining security obligations.
A documented incompatibility can reopen only the affected choice; no runtime
compatibility, license artifact approval or hardware result is fabricated.

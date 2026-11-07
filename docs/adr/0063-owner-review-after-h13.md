# ADR-0063: Pause after H13 for owner testing before Phase 2

- Date: 2026-11-06 America/Sao_Paulo (2026-11-07 UTC)
- Status: Accepted — explicit owner instruction; Phase 2 approval pending
- Supersedes: ADR-0004 automatic continuation from G1 into Phase 2

The owner explicitly requested that development proceed through H13 so they can
test the foundation, and that B01 onward begin only after their approval.
This is an owner-defined execution boundary, not an inferred safety approval.

Continue all authorized foundation implementation, dependency installation,
failure diagnosis, verification and publication through H13. Do not stop the
current H07 build or request routine permission for H08-H13. At H13, require
the actual G1 evidence and deliver the foundation ISO/SHA-256, component/source
inventory, test evidence, reproducible build and recovery instructions, known
limitations, commit and dashboard reference. Leave hardware qualifications
explicit and provide concrete instructions for the owner's testing.

After that delivery, pause implementation and wait for explicit owner approval
before starting B01 or any other B story. Passing G1, elapsed time, silence or
the earlier one-start instruction is not Phase 2 approval. Record the approval
when received before resuming that phase.

The complete planned experimental desktop/agent/installer release and its
acceptance criteria remain unchanged. H13 is an interim foundation delivery;
do not mark the full release goal complete at that point. If goal-state tracking
is active, honor this requested pause when the H13 boundary is actually reached.
The present foundation goal remains active until that boundary or another
explicit owner instruction.

Alternative rejected: automatically starting B01 after G1 would violate the
newer owner instruction. Pausing immediately would also be incorrect: the owner
expressly asked for development through H13 first. Durable repository context
preserves this boundary across session interruptions without workstation RAG.

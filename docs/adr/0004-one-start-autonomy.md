# ADR-0004: One-start autonomous delivery

Date: 2026-11-05
Status: Amended by [ADR-0063](0063-owner-review-after-h13.md) — automatic Phase 2 progression is superseded; foundation autonomy remains.

## Decision

After the owner starts development, the AI proceeds through both phases, installs dependencies, fixes routine failures, validates milestones and updates Git without repeated continuation requests. G1 remains a technical acceptance gate, not a second human approval gate. Report progress without requiring replies. Preserve checkpoint/next-action state across interruptions.

## Limits and completion

Missing credentials, paid resources, legally required acceptance and destructive host-disk actions may require user participation. Respect runtime limits and distinguish pending physical validation from proven results. Never lower acceptance criteria or invent evidence merely to finish unattended. This plan change does not itself start a build.

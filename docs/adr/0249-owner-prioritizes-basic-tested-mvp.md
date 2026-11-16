# ADR-0249: Owner prioritizes a basic-tested MVP

Date: 2026-11-16
Status: Accepted by explicit owner instruction

## Decision

The owner explicitly requested only basic testing and delivery of the complete
MVP today, accepting lower quality and incremental bug fixes after delivery.
This supersedes broader preview validation as a prerequisite for an honestly
labeled MVP. It does not assert that unfinished features or unrun tests passed.

Prioritize the existing implemented product and actual downloadable media over
additional test harnesses, visual refinement, repeated suites, language/provider/
hardware matrices, soak tests or optional edge-case qualification. Reuse unchanged
evidence. Run focused basic checks for changed behavior and repository delivery.

The minimum delivery path is actual boot/login, usable desktop and assistant,
one real task and Stop, plus a blank-virtual-disk installation and installed boot
when publishing an installable image. Preserve disk identity, credential
protection, authorization, cancellation and recovery essentials. Do not format
physical disks or weaken global security. Existing accepted foundation evidence
and artifacts remain unchanged.

Ship with exact artifacts/checksums, brief use/recovery instructions and explicit
known bugs, unavailable functions and untested paths. Deferred coverage belongs
in the owner-use backlog. Keep full B-story/G2 acceptance separate from this MVP;
do not increase accepted progress or claim stable/physical acceptance by waiver.
The target is delivery today, not a guarantee that an unbuilt artifact exists.

## Execution

Keep one guest writer and three isolated source workers. Complete the current
protected-model input correction, run a short real graphical smoke, then produce
and boot the media using the existing image/installer pipeline. Resolve only
failures on that critical path; checkpoint independent blockers and deliver the
actual usable scope with limitations instead of inventing acceptance.

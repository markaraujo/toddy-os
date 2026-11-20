# Current Phase 2 delivery execution

Updated: 2026-11-20, America/Sao_Paulo.

The single bounded generation8 local graphical ISO cut is **closed after a failed
compression gate**. Its329-package qualification, independent full-root review,
nine-check finalization and live staging passed. The coordinator then ran native
`dconf read` against the finalized writable root; Dconf created runtime state
under `/run/user/0/dconf` after its assembly snapshot. The exact-image gate
correctly rejected that drift before creating compression output. No retry or
second generation was attempted. See the [checkpoint](PHASE-2-CHECKPOINT.md) and
[generation8 evidence](evidence/B06-generation8.md).

No ISO, graphical ISO boot, installation, B06/G2 acceptance or public download
exists from this cut. Preserve generation8 and generation6/7 evidence. The next
safe source/procedure change is to execute post-finalizer native Dconf queries
only in a disposable overlay. A future separately authorized cut must remeasure
capacity and use a fresh unique generation. The general delivery sequence below
is background planning; it does not reopen this closed attempt or authorize
B07–B13 work under the current bounded request.

## Small verified slices

| Slice | Entry condition | Acceptance and stop condition |
| --- | --- | --- |
| 0. Space and source admission | Immutable signed inputs and previous failures retained | Recheck the measured root/compression bound and both free counts before a new root. Old copies are already retired only after complete host proof. The targeted dconf command and mode readback passed in a disposable overlay. Stop if guest capacity is below the measured gate; recalculate the ISO gate from actual media inputs before its write. |
| 1. Fresh live root | Slice 0 passed; existing failed root preserved; reviewed inputs unchanged | One new generation unpacks, qualifies, passes independent review, finalizer and live stage. Save actual receipts, package count, root identity, command exits and logs. Stop on uncertain postconditions; never replay an intent. |
| 2. Graphical local preview | Slice 1 accepted; finalizer and media inputs verified | Boot isolated candidate in QEMU/KVM; capture real login, desktop, Toddy entry, basic text/Stop and failure states. Owner can interact with the isolated VM. Record absent features honestly. |
| 3. Installed local preview | Slice 2 accepted; blank test disk and installer prerequisites verified | Install to a designated disposable virtual disk, boot twice without ISO, and check persistent user data/settings and target identity. Stop before writes if disk identity differs. |
| 4. Remaining B stories | Follow `status.json` dependencies and existing acceptance criteria | Implement B06–B12 in small independently checked slices. B07/B10 can proceed when useful without a second guest writer. Do not count untested work as complete. |
| 5. B13/G2 public delivery | B01–B12 accepted and B13 in progress with final ISO evidence | Use `docs/RELEASES.md` and the Phase 2 handoff utility for immutable artifacts, checksums, source/license inventory, GitHub prerelease and portal verification. Physical hardware remains a separate claim. |

One agent owns all guest/image writes. Parallel subagents may audit capacity,
review source/tests and maintain documentation in separate paths. The coordinator
integrates one reviewed change at a time before syncing source to the guest.
No subagent starts a second native writer or clears evidence. Set a bounded task,
expected artifact and stop condition for each agent; avoid a fixed worker count
or calendar deadline for unmeasured build and boot work.

For each slice, save exact inputs, elapsed time, commands, exit status,
postconditions, log path and next action in the checkpoint. Apply the bounded
failure policy in `AGENTS.md`: one unchanged transient retry; after two failed
corrections or 30 minutes on the same cause, stop that slice and move to eligible
independent work. A healthy long build is monitored, not restarted. Use focused
checks, then `make check` for repository changes. Preserve the 16 GiB guest
reserve and use the temporary host reserve only where ADR-0251 permits it.

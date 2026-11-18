# Current Phase 2 delivery execution

Updated: 2026-11-18, America/Sao_Paulo.

The next deliverable is a **local, explicitly interim owner preview** of the
graphical VM. It is not B13/G2, an installable release, or a public download.
Installer9, signed export8, inputs4 and generation7 have passed native package,
resource and finalizer gates. The live stage stopped on the 0600 mode of the
generated Toddy dconf database; its intent and journals are retained, and its
partial root now has complete verified host custody. Earlier failed roots have
separate verified custody. The current slice is stopped after
two live-stage corrections. See the [current checkpoint](PHASE-2-CHECKPOINT.md)
and [generation7 evidence](evidence/B06-generation7.md). The next slice must
recheck the root/compression capacity before creating another root, then attempt
one fresh stage with the exact mode correction. The ISO gate is measured from
actual compressed/initramfs sizes before its write. No ISO or boot claim
follows from package/finalizer success.

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

# Current Phase 2 delivery execution

Updated: 2026-11-18, America/Sao_Paulo.

The next deliverable is a **local, explicitly interim owner preview** of the
graphical VM. It is not B13/G2, an installable release, or a public download.
The MVP live roots `toddy-mvp-live-image-1` and
`toddy-mvp-live-image-3` now both have uncertain resource operations and remain
frozen. Generation 3 unpacked 329 packages but qualification failed without a
receipt. Never replay their intents, copy either root into a future generation,
or treat partial cache output as acceptance. The first slice is stopped until
the cache provenance/package chain and a measured new-root capacity path are
resolved. See the [blocker audit](PHASE-2-BLOCKER-AUDIT-2026-11-18.md).

## Small verified slices

| Slice | Entry condition | Acceptance and stop condition |
| --- | --- | --- |
| 1. Fresh live root | Host/guest capacity measured; existing failed root preserved; reviewed inputs unchanged | New generation unpacks and qualifies resources once. Save actual receipt, package count, root identity, command exit and log. Stop on uncertain postconditions; reconcile before any retry. |
| 2. Graphical local preview | Slice 1 accepted; finalizer and media inputs verified | Boot isolated candidate in QEMU/KVM; capture real login, desktop, Toddy entry, basic text/Stop and failure states. Owner can interact with the isolated VM. Record absent features honestly. |
| 3. Installed local preview | Slice 2 accepted; blank test disk and installer prerequisites verified | Install to a designated disposable virtual disk, boot twice without ISO, and check persistent user data/settings and target identity. Stop before writes if disk identity differs. |
| 4. Remaining B stories | Follow `status.json` dependencies and existing acceptance criteria | Implement B06–B12 in small independently checked slices. B07/B10 can proceed when useful without a second guest writer. Do not count untested work as complete. |
| 5. B13/G2 public delivery | B01–B12 accepted and B13 in progress with final ISO evidence | Use `docs/RELEASES.md` and the Phase 2 handoff utility for immutable artifacts, checksums, source/license inventory, GitHub prerelease and portal verification. Physical hardware remains a separate claim. |

One agent owns all guest/image writes. Independent source or documentation work
may overlap only when resource and lock budgets permit. There is no fixed worker
count or calendar deadline for unmeasured build and boot work.

For each slice, save exact inputs, elapsed time, commands, exit status,
postconditions, log path and next action in the checkpoint. Apply the bounded
failure policy in `AGENTS.md`: one unchanged transient retry; after two failed
corrections or 30 minutes on the same cause, stop that slice and move to eligible
independent work. A healthy long build is monitored, not restarted. Use focused
checks, then `make check` for repository changes. Preserve the 16 GiB guest
reserve and use the temporary host reserve only where ADR-0251 permits it.

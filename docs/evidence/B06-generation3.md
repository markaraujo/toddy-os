# B06 MVP live generation 3: stopped after resource failure

Date: 2026-11-18 UTC. This is failure evidence, not B06, ISO, boot or G2 acceptance.

- Source commit at guest sync: `0e0f790`. Candidate source hashes for `image_assemble.py`, `native_finalizer.py` and `grow_candidate_target.py` matched the host. The first sync stopped before transfer because the Ubuntu guest has `/var/log` mode 775, root:syslog; the old guard rejected it. The exact-parent correction was committed, validated and synced under the exclusive input lock. The Ubuntu mode was restored and the new guard passed. Logs: `.local/phase2/candidate-sync-generation3.log`, `.local/phase2/candidate-sync-generation3-fixed.log`.
- With the VM's normal kernel filesystems mounted, an isolated target `dconf compile` produced SHA-256 `5d86fa8e8e16c157ec30cc9e2cca4fe71d50b580d1932936894b927036100cb4`, matching the declared output. Generation 1 was only read.
- `image_native.sh mvp-live` exited 0 and recorded `native-archives-unpacked-needs-resource-qualification`, 329 configured packages, root `/sources/stage/toddy-mvp-live-image-3/root`, inode 10804160, required preflight 26,031,034,368 bytes. Log: `.local/phase2/mvp-live-unpack-3.log`.
- `image_native.sh qualify-mvp-live` exited 1 after creating generation 3 `resource-intent.json`. The exception was `installer_native_command_failed` in the cache producer loop. No `candidate-resource-receipt.json` exists. The dconf output matched the declared hash; GDK/GTK caches and depmod files changed. The first failing command cannot be proven from the suppressed stderr. Log: `.local/phase2/mvp-live-qualify-3.log`.
- Read-only comparison showed depmod outputs matching declared hashes; the GDK/GTK caches differed. The next planned output, `hwdb.bin`, kept its older timestamp. Isolated disposable overlay runs of dconf, GDK/GTK, depmod, hwdb, schemas, icons and MIME commands exited 0, so they did not reproduce the protected namespace failure. Those probes wrote only temporary overlay upper layers, which were removed; they did not qualify the candidate root.
- After failure, target free space was 26,511,298,560 bytes. The Candidate VM stopped cleanly; accepted backings were rechecked by its stop guard. Both generations 1 and 3 are preserved with their intents. Neither is eligible for command replay or custody retirement.

Next action: capture the exact failing producer and bounded stderr in a disposable overlay under the image wrapper's protected mount namespace. Resolve any actual cache output drift. Measure additional target space before creating another fresh root; the current margin over the one-root preflight is only about 480 MiB. Use a new generation only after the failure and capacity have been independently reconciled.

## Continued read-only analysis

Protected mount-namespace overlay probes on 2026-11-18 reproduced the wrapper's
stage/source topology and clean environment. All fixed cache commands exited 0,
including a probe with the cache outputs restored from the exact package bytes.
This does not identify the original first nonzero command, because the root had
already acquired partial effects. The source now records the first failing fixed
command in a new private failure file for future generations; no command was
replayed in generations 1 or 3.

The selected GDK and GTK package caches have SHA-256 values
`756bea55f0aada7f6750be7489bd3b7306ae47ddb298b5735586a14e1cd3af9f`
and `ca7ca0c62312109e0cf29107c4f9be5d28e6a404c93d50fe0ff86d9e21355828`.
Their exact `.deb` members match those values. Native regeneration instead gave
`2d9a6920934ee24d197b5a27bc8fcd3cb3628df46301e52ea066f775631f6fa1`
and `c621b3f0b769200694a3244a1208a471ec388823f827a8692980b5a6f755f70c`.
The differences are a trailing blank line (GDK) and a module-path comment plus
trailing newline (GTK). The current signed inputs require regeneration, so both
are independent acceptance blockers even if every command returns 0. See the
[blocker audit](../PHASE-2-BLOCKER-AUDIT-2026-11-18.md) for the full correction chain.

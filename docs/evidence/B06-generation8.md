# B06 generation 8: passed live staging, blocked compression

Executed 2026-11-18; cold handoff reconciled 2026-11-20 (America/Sao_Paulo).
This bounded cut is closed. No ISO or graphical ISO boot exists from this attempt.
B06 remains in progress, B07–B13 remain unstarted and G2 remains pending.
The [machine-readable receipt](B06-generation8.json) contains exact inputs,
command timestamps, output identities and raw evidence SHA-256 values.

## Initial reconciliation and admission — passed

- Initial checkout: clean `main`, `fecedfa118f607e52d66d495a84e0549473a3573`,
  matching `origin/main`. Work moved to `b06/local-iso-generation8`,
  [PR #2](https://github.com/markaraujo/toddy-os/pull/2); main was not changed.
- After the host restart, the retained Candidate container was exited0 and no
  QEMU/guest writer remained. Both candidate qcow2 checks passed. All accepted
  foundation/B02 backing identities matched their recorded identities. Only the
  exact retained Candidate container was restarted; overlays were not recreated.
- The target was the designated 204 GiB `TODDY-LFS-TARGET`, ext4 UUID
  `e7726c1a-8f91-445f-96ac-88721b58caf8`. Initial guest free space was
  41,193,058,304 bytes; host free space was approximately 116.3 GB.
- Export8's 920 files, including 329 packages and both signatures, matched their
  retained host copies. Both signatures were verified again with `gpgv`.
  Native `PreparedPayload._load()` checked all selected archives, records and
  signed repository custody. Inputs4 and generation6/7 guard hashes were compared
  again at the end and remained unchanged. No old intent was replayed.
- A disposable native overlay verified targeted `dconf compile`, output path,
  content, root:root ownership, single-link regular file and mode0644. Native
  reads in that disposable overlay returned `true`, `false` and `uint32 0` for
  the three declared settings. Its lower dconf tree was unchanged; no IBus
  database was generated. Output SHA-256:
  `b7afc3830f61d8c9180161c6c1bfef4d31dd42dab8d2fdb9ae92966e7c6ba010`.
- Explicit MVP planned adoption used allocation factor1. Root admission required
  26,031,038,464 bytes versus 41,193,054,208 available. The forecast compression
  margin also passed. Fresh generation8, reviewed-generation8 and all three
  media output slots were absent. The coordinator was the sole guest writer;
  a second agent independently reviewed source, capacity and actual evidence.

Only fixed current-generation route references changed; historical generation6/7
custody profiles remained intact. Source commit `d72dfda` matched six actual
coordinator source files in the guest after exclusive-lock synchronization.

## Actual commands and results

The single writer used transient systemd units with separate append-mode job
logs. Each action below was dispatched once through:

```sh
bash /opt/toddy-build/scripts/build/phase2/image_native.sh ACTION
```

| Action | Actual result | Observed postcondition |
| --- | --- | --- |
| `mvp-live` | **Passed**, exit0, 70 s | 329 configured packages; empty Dpkg audit; fresh root inode10943709 |
| `qualify-mvp-live` | **Passed**, exit0, 50 s | 19 cache outputs, zero blockers |
| Independent full-root review | **Passed**, exit0 | 150,280 entries, exact generated map and complete-image hash match inputs4 |
| `adopt-finalize-mvp-live` | **Passed**, exit0, 73 s | Same root inode adopted; all nine actual finalizer checks passed; reports copied and hash-verified |
| `stage-mvp-live` | **Passed**, exit0, 85 s | Own live receipt/journal; 19 attributed delta entries; complete 150,294-entry media snapshot including ACL sidecar |
| Read-only compression capacity admission | **Passed**, exit0 | Actual expanded bound6,837,329,920 bytes; required33,002,012,672; free34,926,219,264; margin1,924,206,592 |
| `media-mvp-compress` | **Failed**, exit1, 25 s | `Actual image differs from final assembly`; rejected before compression slot creation or native compressor dispatch |
| Native SquashFS/extraction, initramfs and ISO | **Not executed** | No media artifacts or artifact hashes exist |
| QEMU/KVM ISO boot; login, desktop, Toddy entry | **Not executed** | No graphical boot or assistant interaction claim |
| Installation; B06/G2 acceptance | **Not executed** | No installation/release acceptance |

The independent review reproduced complete-image SHA-256
`fcdd70749575fc562fddc007d9a38f8f92d09fd16eb0ae34421737cdd2eb5941`
and generated-map SHA-256
`93b6042c5f3cae9ee0dff2142182e9729f32537f646acf7b9fc15c4bdb33af26`.
The final live media manifest, before observer drift, was
`bd5c3f319af634949d3a2fe2433095a60c23d7145d5cf4c547479491a44af93e`.
These are root/manifest hashes, not ISO hashes.

## Failure cause and preserved state

After live staging, the coordinator verified the actual database using native
`dconf read` inside the **writable finalized root**, while the separate read-only
compression admission was snapshotting it. Although the CLI operation was a read,
Dconf initialized root's runtime state. This observer changed the image after
its final snapshot; the post-finalizer query needed a disposable overlay.
The earlier disposable probe was isolated correctly. The coordinator's later
verification procedure caused this failure.

The independent drift audit found exactly four unknown paths:

```text
/run/user
/run/user/0
/run/user/0/dconf
/run/user/0/dconf/user
```

The directories were root-owned0700; the last file was root:root0600, two bytes,
SHA-256 `96a296d224f285c67bee93c30f8a309157f0daa35dc5b87e410b78630a09cfc7`.
Only `/run`'s mtime changed among existing entries. There were no missing entries
and hardlink classes still matched. Actual entries increased from150,294 to150,298.
The native Toddy dconf database itself retained its correct content and0644 mode.

The exact-image gate correctly rejected the changed root. No runtime path was
removed, no assembly manifest was refreshed, no compression was retried and no
second generation was created. The retained guest root is:

```text
/mnt/lfs/sources/stage/toddy-mvp-live-image-8-reviewed/mvp-live-root-2
```

Its intents, finalizer/live receipts, original snapshots, drift and unit logs
remain evidence. The compression, initramfs and ISO output directories are absent.
Full small receipts/reports and raw logs were copied to
`.local/phase2/b06-generation8/`. The failure log SHA-256 is
`8b073a085ccf53cfec4baac26f4ba8510c7e72006bbc491eadb4daf12962652e`;
the drift audit SHA-256 is
`e036cdc5e59fcf2b6c1501d82158f805a0d421cd35ae80a5dc163bbba73126e1`.
The JSON receipt inventories remaining evidence hashes.

## Repository checks and final handoff

`python3 -m unittest tests.test_mvp_image_slots tests.test_live_session
 tests.test_candidate_root_custody` passed34 focused tests. The initial focused
run exposed one stale generation7 expected value, which was corrected without
changing historical custody expectations. Source `make check` passed1199 tests
in23.533s. Two private read-only admission harness calls failed before image
writes (wrong module import, then a `verify_payload` call requiring an actual
finalizer); both failed logs remain, and the corrected `_load()` custody check
passed. These are not successful native image operations.

At the 2026-11-20 handoff, the Candidate container was cold/exited0, no QEMU or
writer was active, both qcow2 structure checks passed again and accepted backing
identities were unchanged. The VM was not restarted for this documentation
handoff. Last measured guest free space was34,926,223,360 bytes on2026-11-18;
current host free space was116,035,272,704 bytes before handoff file generation.
The final repository `make check` passed1199 tests in24.860s, with planning,
local links and generated progress checks passing; its log hash is in the JSON
receipt.

**Exact next action:** review this preserved drift and move all post-finalizer
native Dconf queries into a disposable overlay. Only a separately authorized
future cut may remeasure capacity and select a fresh unique generation. Do not
repair/retry generation8, replace its final manifest, replay generation6/7 intents,
or infer ISO/boot acceptance from the passed package/finalizer/live receipts.

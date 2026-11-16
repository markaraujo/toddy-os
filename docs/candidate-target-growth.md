# Exact disposable candidate target growth

Source only: no QMP, VM/device operation, resize or guest call was run to prepare
this slice. The coordinator is the sole writer. This changes ONLY the current
candidate top overlay from180GiB to204GiB, never an accepted B02/foundation image
or a physical host disk. The original kernel/ISO acceptance remains unchanged.

The coordinator's read-only snapshot identified `/dev/vdb`, serial
`TODDY-LFS-TARGET`, GPT ID `D0DEB477-38D0-41A4-A76D-99F68B865452`, partition4 start
17831936, PARTUUID `5e491ca4-ea89-4e55-94b3-cb0b3fcc4694`, ext4 UUID
`e7726c1a-8f91-445f-96ac-88721b58caf8`, label `TODDY_LFS`, mounted `/mnt/lfs`.
The exact original four partitions/types/names/UUIDs are frozen in
[candidate_target_geometry.py](../scripts/build/phase2/candidate_target_geometry.py).
Only partition4 length changes, by exactly24GiB; start, all UUIDs and partitions1-3
are preserved. GPT headers move to the new end, maintaining the original2048-sector
end alignment margin. No formatter, loop device, zeroing or shrink exists here.

## Capacity and source custody

The host must have **100GiB+512MiB plus ALL24GiB** available on the candidate image
filesystem before effect admission (133680857088bytes). Actual QCOW allocation
and host free bytes are recorded separately; a sparse virtual-size change is not
claimed to preallocate physical space. Continue measuring actual host/guest free
space before each later image/bundle stage. The absolute host cold reserve stays
100GiB+512MiB and the guest's16GiB build floor is not reduced. The source does not
promise that arbitrary future writes fit just because the resize passed.

Commit and sync the three reviewed growth source files and `scripts/build/target.sh`
through the existing verified metadata route. Do not sync or edit helpers during
a running/prepared growth: exact host/guest source/tool hashes are retained. Wait
for the healthy current compiler/qualifier to finish; never interrupt it to obtain
the lock. No other native/package writer or boot probe may overlap the operation.

## Preferred live QMP flow

From the clean host checkout, as its ordinary user:

```sh
python3 scripts/host/phase2_candidate_target_grow.py inspect
python3 scripts/host/phase2_candidate_target_grow.py grow
```

The existing candidate `owned()`/`bases()` checks authenticate Docker labels,
loopback SSH port, canonical read-only entire `/vm` backing mount and writable
candidate directory. QMP drive ID must be exactly `lfs`, top image exactly
`/vm/phase2-candidate/lfs-target.qcow2`, qcow2, backed by the accepted read-only
`/vm/phase2/lfs-target.qcow2`. Original immutable backing identities and already
retained complete backing hashes are reused; unchanged large images are not
rehashed as an unrelated preview gate. No arbitrary path/device/size is accepted.

The guest acquires the EXISTING global build lock and retains a durable running
marker. It checks the exact VM/builder serial, root `/dev/vda1`, target serial,
filesystem/partition UUID, mount and complete old GPT. Both raw GPT areas, partition
dump, ext4 geometry, source/tool hashes and full-root file snapshot are retained
before the host is allowed to call QMP. The host calls `block_resize` ONCE, for
`lfs`/219043332096bytes, then rechecks actual QMP geometry before notifying the
same still-leased guest. Kernel disk-size notification is polled read-only;
QMP is never retried when a reply is uncertain.

The guest performs an actual native sfdisk dry run, then one exact GPT write with
`--no-reread --no-tell-kernel --lock=yes --wipe=never --wipe-partitions=never`.
The fixed input preserves all other partitions and disables signature wiping.
Both GPT header/entry-array CRCs, replica agreement, exact resulting table and
existing BIOS MBR boot code are checked. `partx --update --nr 4 /dev/vdb` updates
ONLY kernel partition4. The filesystem step is NOT admitted unless the kernel
reports the precise new partition size. `resize2fs /dev/vdb4` then grows mounted
ext4 online. Native command intents, exact inputs, logs and actual exits are
retained separately; no failed exit is reclassified.

Afterward the guest checks disk/kernel/GPT/ext4 geometry and UUID again, compares
a second full-root snapshot to the first, and requires zero existing file/mode/
ownership changes. Root-owned completed evidence is written only after every
step passes. No automatic retry occurs, and the host never kills a potentially
committing guest resize merely to meet a response timeout.

## Cold fallback only when required

If QMP lacks `block_resize`, the live command refuses before starting a growth
intent. The same exact source supports this concrete cold sequence:

```sh
python3 scripts/host/phase2_candidate_target_grow.py cold-prepare
python3 scripts/host/phase2_candidate_vm.py stop
python3 scripts/host/phase2_candidate_target_grow.py cold-resize
python3 scripts/host/phase2_candidate_vm.py start
# Inspect actual SSH readiness and mounts with the existing owned() channel.
python3 scripts/host/phase2_candidate_target_grow.py cold-finish
```

Cold prepare saves the same old GPT/full-root/identity evidence and leaves the
running marker to block unrelated jobs. Cold resize requires the authenticated
clean stop receipt, exact cold overlay identity/backing, no candidate container,
host budget and one-shot host intent before running native-container `qemu-img
resize` against ONLY that top overlay. It checks the actual exit/new image size
and unchanged accepted backing. The existing controller restarts the VM; no
foundation image is resized/recreated. Cold finish requires a genuinely NEW guest
boot ID, the original exact source/tool/intent/snapshot hashes and unchanged old
partition geometry. It performs the same guarded GPT/kernel/ext4 growth and
independent root-file comparison. Lost read-only source bind mounts after reboot
must be re-established separately from their original verified holders when a
later component actually needs them; no old compiler job is replayed here.

## Durable completion and guarded later work

Host state lives under `.local/vm/phase2-candidate/target-growth-1/`. Private guest
raw-GPT/full-root/command evidence is under
`/var/log/toddy/phase2/candidate-target-growth-1/`; the existing global running
marker is `candidate-target-growth-1.running.json`. Keep these, all failed evidence
and actual allocation measurements. A new root-owned public metadata receipt
`/var/log/toddy/phase2/candidate-target-growth-qualified-1.json` is mode0644 and
contains no personal content.

Historical180GiB `guard_guest` behavior remains unchanged. The exact204GiB branch
requires that completed receipt and revalidates current producer hashes,
serial/UUID/mount, exact GPT/CRC, kernel partition and ext4 sizes. Any other size,
missing/partial/unprivileged receipt or running marker refuses ordinary jobs.
This is a fixed qualification path, not a generic size override.

The audit found no independent180GiB limit in the current candidate, assistant
hook/control, voice or image path. The old `vm.py`180GiB initial foundation
creation and `boot_test.py` standalone historical180GiB checkpoint guard remain
unchanged. They must not be repurposed to rebuild or relabel the new candidate.

## Failure/recovery boundary

Never repeat `grow`, cold-resize, a GPT write or resize2fs from chat memory or an
SSH/QMP acknowledgement alone. An existing context/marker/path refuses replay.
Inspect host state/QMP (or cold `qemu-img info` through the existing read-only
custody tooling), private command intents/exits, actual block sizes, raw GPT,
UUID, ext4 block count and full-root snapshots first. If partition/kernel update
fails, ext4 growth is withheld. If ext4 geometry already grew, NEVER restore an
old smaller GPT or shrink the image. If QMP grew but the guest did not admit GPT,
preserve the exact old/new state; a separately reviewed reconciliation must
finish only genuinely missing steps. The cold path starts from its own verified
cold preparation; it is not a bypass for an uncertain live operation.

A host timeout may leave a healthy guest resize running. Monitor its actual
process/marker/evidence; do not kill it, delete receipts or clear the global
marker merely to resume another job. A fully completed private receipt with an
interrupted final transport still needs actual host/backing/reserve reconciliation
before acceptance. Final cold checkpoint and independent image/installed-boot
integrity remain required later. Source fixtures below are not native growth,
recovery or G2 acceptance:

```sh
python3 -m unittest discover -s tests -p test_candidate_target_growth.py -v
```

Native CLI semantics were checked against cached util-linux2.42.4 source/manpages
for sfdisk and partx: GPT relocation on write, no signature wiping, explicit
kernel resize ioctl for the selected partition. Actual builder tools are pinned
by path/hash in the intent; an unsupported native command fails before its next
step rather than silently changing tools or versions.

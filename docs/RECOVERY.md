# Development recovery

Current checkpoint: H03 target preparation, package ownership and runner tests passed in the real KVM guest. Target root is /dev/vdb4 mounted at /mnt/lfs; H04 cross-toolchain and target-linked C checks passed.
No ISO exists. Gate G1 and G2 remain pending. Inspect status.json and actual
processes before continuing; this document is updated at verified boundaries.

## VM lifecycle

```sh
python3 scripts/host/vm.py inspect
python3 scripts/host/vm.py ssh 'hostname; lsblk -o NAME,SIZE,SERIAL,MOUNTPOINTS'
python3 scripts/host/check_requirements.py
```

Container: toddy-builder. SSH: loopback port 2222. Private identity and
known_hosts: .local/vm/; never commit or include these in an image.
Serial log: .local/vm/serial.log (replaced on restart).

Use python3 scripts/host/vm.py stop for a clean shutdown; it waits for QEMU to
exit and removes the stopped container. Use start to resume. If a container
has already exited, inspect docker logs and its exit status before removing
only that container. Do not remove disk files or recreate a working target.

An offline copy of the configured builder is at
.local/vm/checkpoints/h01-builder.qcow2. Its backing image is
.local/vm/builder-base.img, exposed at /vm/builder-base.img inside QEMU's
container. Restore the copy only while the guest is stopped; preserve the
failed overlay first. H03 adds a paired builder/target checkpoint.
The checkpoint is a convenience on the same disk, not disaster recovery.

Latest paired offline checkpoint: .local/vm/checkpoints/h03-builder.qcow2 and
h03-target.qcow2. Restore both together with QEMU stopped, preserving the failed
disks first. The H01 checkpoint predates target preparation.

## Latest verified checkpoint and next action

H04 passed: driver exit 0, five recipe/postcheck successes, retained full logs
and manifests. Latest paired offline checkpoint:
.local/vm/checkpoints/h04-builder.qcow2 and h04-target.qcow2. Both copies were
made with QEMU stopped. The guest is restarted with its target mount and swap
in fstab. Confirm them before any new recipe. See docs/evidence/H04.md.

H05 is next: synchronize reviewed chapter 6 scripts, then start its driver.
The job PID/log/exit files are /var/log/toddy/h05-driver.pid,
h05-driver.log and h05-driver.exit. Never launch a duplicate driver. Inspect
processes and all per-package recipe/postcondition records before completion.

```sh
python3 scripts/host/vm.py ssh 'source /opt/toddy-build/scripts/build/target.sh; guard_target; swapon --show'
python3 scripts/host/vm.py ssh 'cat /var/log/toddy/h05-driver.log; ls /var/log/toddy/build/h05-*'
```

The source-directory mode issue is corrected in current scripts and H04
checkpoint. If restoring the older H03 pair, synchronize current scripts,
restore chmod 1777 /mnt/lfs/sources, and rerun idempotent target preparation
before continuing. Transfer with sync_build.py; it preserves directory modes.

## Storage and resource boundaries

Only .local/vm/lfs-target.qcow2 is the disposable OS build disk. In the guest
its serial must be TODDY-LFS-TARGET. The root disk has TODDY-BUILDER serial.
Never pass workstation block devices into QEMU. Retain 100 GiB host reserve,
begin with 8 compiler jobs, and stop on memory/disk pressure. Before any disk
operation verify hostname, virtualization, serial, capacity and mounts.

# Development recovery

Current checkpoint: H03 target preparation, package ownership and runner tests passed in the real KVM guest. Target root is /dev/vdb4 mounted at /mnt/lfs; H04 binutils pass 1 has passed; GCC pass 1 is running.
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

## Current running job

H04 driver in the guest: PID file /var/log/toddy/h04-driver.pid (read the
actual PID, do not assume it is live). Driver log /var/log/toddy/h04-driver.log;
exit file /var/log/toddy/h04-driver.exit exists only after an observed finish.
Per-package records: /var/log/toddy/build/h04-*. Running GCC log:
/var/log/toddy/build/h04-gcc.log. Inspect process, exit code and postconditions;
do not relaunch while the driver runs. The driver continues through headers,
glibc and libstdc++ only after each prior recipe/postcheck passes.

Known correction after the H03 checkpoint: source transport had reset the
sources directory to 0755. Restore chmod 1777 /mnt/lfs/sources before building;
the corrected prepare-target script checks lfs write access. Use sync_build.py
to transfer archives without overwriting directory metadata. The paired H03
checkpoint predates this correction; after restoring it, synchronize corrected
scripts and rerun idempotent target preparation before restarting H04.

## Next action

H02 source integrity freeze is complete. The source downloader logs to
.local/logs/fetch-sources.log and captures exit status in
.local/logs/fetch-sources.exit. Inspect its process and result before retrying.
The resumable command is python3 scripts/fetch_sources.py. Verified archives
are reused; mismatches are rejected, never extracted. Start H04 with frozen LFS chapter 5, deriving and reviewing each recipe.
Build via /opt/toddy-build/scripts/build/run_step.py in the guest; logs, manifests
and running/failed/success records are at /var/log/toddy/build. An interrupted
running record requires inspection of partial installation before retry.

## Storage and resource boundaries

Only .local/vm/lfs-target.qcow2 is the disposable OS build disk. In the guest
its serial must be TODDY-LFS-TARGET. The root disk has TODDY-BUILDER serial.
Never pass workstation block devices into QEMU. Retain 100 GiB host reserve,
begin with 8 compiler jobs, and stop on memory/disk pressure. Before any disk
operation verify hostname, virtualization, serial, capacity and mounts.

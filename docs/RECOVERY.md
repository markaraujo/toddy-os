# Development recovery

Current checkpoint: H05 completed all 17 temporary-tool steps, library/ownership audit and interruption/restart checks. Target root is /dev/vdb4 mounted at /mnt/lfs.
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

H05 passed: driver exit 0, 17 recipe/postcheck successes and verified full log
hashes. Latest paired offline checkpoint:
.local/vm/checkpoints/h05-builder.qcow2 and h05-target.qcow2. Copies were made
with QEMU stopped. H05 failed gzip attempt is retained under runner history/;
its verified retry succeeded. See docs/evidence/H05.md.

H06 is next/running: synchronize reviewed chapter 7 scripts, start its driver
only once, then inspect actual processes. PID/log/exit files:
/var/log/toddy/h06-driver.pid, h06-driver.log and h06-driver.exit. Per-package
records live at /var/log/toddy/build/h06-*. The bootstrap changes lfs ownership
to root, mounts guest pseudo filesystems and checks actual native C/C++ in
chroot. Later steps build eight temporary packages and remove /tools.

```sh
python3 scripts/host/vm.py ssh 'cat /var/log/toddy/h06-driver.log; ls /var/log/toddy/build/h06-*'
```

If interrupted, inspect the failed/running record and manifest before retry.
Do not run native chroot recipes directly on the builder root or workstation.
The H05 pair is the rollback point before ownership/chroot transition. A
future H06 completion also requires a demonstrated checkpoint restoration.

## Storage and resource boundaries

Only .local/vm/lfs-target.qcow2 is the disposable OS build disk. In the guest
its serial must be TODDY-LFS-TARGET. The root disk has TODDY-BUILDER serial.
Never pass workstation block devices into QEMU. Retain 100 GiB host reserve,
begin with 8 compiler jobs, and stop on memory/disk pressure. Before any disk
operation verify hostname, virtualization, serial, capacity and mounts.

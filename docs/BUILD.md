# Current build procedure

This document covers verified H01–H03 and the running H04 implementation.
It is not a complete release build manual yet. No Toddy ISO exists.
Use status.json and the evidence files to distinguish passed milestones from
recipes still under validation. All commands below run from the checkout root.

## Workstation requirements

Linux x86_64, working Docker and access to /dev/kvm, Python 3.12+ (tar data
filter and hashlib.file_digest), OpenSSH client, curl, tar and Git. The QEMU
container installs tools from Ubuntu's trusted package archive and records its
package list. Host package installation is unnecessary on the measured host.
Do not mount the Docker socket or physical block devices into a guest.

```sh
scripts/host/inventory.sh
docker build -t toddy-qemu:h01 -f scripts/host/Dockerfile .
python3 scripts/host/fetch_image.py
python3 scripts/host/vm.py prepare
python3 scripts/host/vm.py start
```

Wait for actual guest SSH and cloud-init completion, inspecting the serial log
if unavailable. The start command only launches QEMU; it does not assert boot
success. Review image hash, disk identity and guest hostname before continuing.

```sh
python3 scripts/host/vm.py ssh 'hostname; cloud-init status; lsblk -o NAME,SIZE,SERIAL,MOUNTPOINTS'
python3 scripts/host/vm.py ssh 'bash -s' < scripts/host/guest-setup.sh
python3 scripts/host/check_requirements.py
python3 scripts/fetch_books.py
python3 scripts/fetch_sources.py
```

Fetched books are in .local/books/lfs/13.1 and .local/books/blfs. Consult the
specific frozen section before each recipe. Review security obligations in
ADR-0007. All sources are verified before extraction; do not use a moving
stable book or substitute package versions without a recorded decision.

## First target preparation

Only this designated VM's blank disk with serial TODDY-LFS-TARGET may be
partitioned. The script validates target identity before any write and aborts
if an unknown filesystem exists. --apply is destructive to that disposable
virtual disk and is authorized for this build; it never runs on physical host
devices. Run the dry plan first and inspect it.

```sh
python3 scripts/host/vm.py ssh 'mkdir -p /opt/toddy-build'
tar -cf - scripts/build config/books.lock.json config/sources.lock.json | python3 scripts/host/vm.py ssh 'tar --no-overwrite-dir -xf - -C /opt/toddy-build'
python3 scripts/host/vm.py ssh 'bash /opt/toddy-build/scripts/build/prepare-target.sh'
python3 scripts/host/vm.py ssh 'bash /opt/toddy-build/scripts/build/prepare-target.sh --apply'
python3 scripts/host/sync_build.py
python3 scripts/host/vm.py ssh 'bash /opt/toddy-build/scripts/build/package-prototype.sh'
```

The runner probe scripts are one-time disposable tests, with fixed step names;
inspect existing marker files before intentional reruns. The source transfer
must preserve the sticky sources directory mode: never transfer a whole
cache directory with metadata overwriting /mnt/lfs/sources.

## H04 cross-toolchain

Recipes follow LFS 13.1-systemd chapter 5 exactly, with integrity verification,
logs, install manifests and explicit postconditions added around the commands.
The eight-job setting is for this build guest, not an architecture tuning flag.
No final compiler/libc test is waived by this temporary build.

```sh
python3 scripts/host/vm.py ssh 'nohup bash /opt/toddy-build/scripts/build/h04-driver.sh > /var/log/toddy/h04-driver.log 2>&1 < /dev/null & echo $! > /var/log/toddy/h04-driver.pid'
python3 scripts/host/vm.py ssh 'cat /var/log/toddy/h04-driver.log; ls /var/log/toddy/build/'
```

Do not launch a second driver while one is running. Inspect the recorded PID
and child processes, driver exit file, each recipe and postcheck result and
manifest before continuing. Exit 0 plus verified postconditions is required;
no exit file or a running marker means unfinished work. Logs survive SSH exit.
On failure, inspect logs and partial target changes before retry; the runner
preserves failed attempts under history/. For interrupted running markers,
archive the record only after diagnosing and recovering partial installation.

## Recovery

See [recovery checkpoints](RECOVERY.md). Stop QEMU cleanly before copying or
restoring images. Keep source archives, images and logs outside Git. Full
rebuild reproducibility and final package/license inventories remain release
acceptance work; the current tooling does not claim byte-identical results.

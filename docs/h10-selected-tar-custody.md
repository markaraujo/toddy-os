# Narrow custody of the historical H10 copy tar

The candidate's old `h10-live-root-evidence` is mostly one opaque native Tar
archive, not another expanded root. This profile can retire only
`/mnt/lfs/sources/stage/h10-live-root-evidence/copy/selected-root.tar` after real
private host compression and complete decompression verification. It never
extracts Tar members or places root-owned/setuid payload on the workstation.
No Docker restore container or extra capabilities are needed for opaque-byte
custody; the original Tar bytes already encode nested permissions, numeric
owners, nanosecond timestamps, xattrs/ACLs, links and file data.

The frozen candidate file is device 64788, inode 8707439, mode 0644, root:root,
link count 1, 3,731,302,400 bytes, allocated 3,731,308,544 bytes and mtime
1794055054388498491 ns. SHA-256:

```text
84bbe95d1dbfe3b50a8284e95006b461c7eab6a3a1091e41bfe519a96fa7898d
```

The guest helper additionally pins evidence/copy directory identities, the
accepted assembly/copy reports, selected and final image manifests and complete
27-row evidence metadata/hash inventory. It rejects symlinks, extra entries,
external hardlinks, nested mounts, loop use, open descriptors or mapped consumers.
The existing target serial/root/mount guards and native build lock remain active.

## Coordinator command

Only the single host coordinator runs this after reconciling active native jobs
and syncing both committed helpers to their fixed paths:

```sh
python3 scripts/host/phase2_h10_selected_tar_custody.py
```

The host entry takes the existing native-boot-test lock, checks the actual
candidate container/port/overlay ownership and unchanged accepted backing
identities, and preserves the configured host free-space reserve plus the full
uncompressed bound. A new private 0700 directory is created at
`.local/phase2/h10-selected-tar-custody-1`. It refuses existing or partial custody.
The fixed candidate SSH command streams the opaque file directly into a 0600
host gzip with timestamp/name normalization. Only bounded chunks enter RAM.

The host flushes and fsyncs the compressed file and directory, checks the actual
successful guest export receipt and fully decompresses every byte into SHA-256
and byte counting. No nested path or executable is interpreted. The original
stream SHA/size must match the retained frozen Tar exactly. The private durable
host receipt records the actual gzip SHA/size and original Tar metadata before
the guest receives a retirement request.

The guest independently rechecks all source pins, complete evidence inventory,
boot identity and absence of consumers, writes/fsyncs `retire-intended`, rechecks
again, and unlinks only that literal Tar pathname. It restores the parent
copy-directory mtime and verifies every remaining report/log/manifest unchanged.
The measured guest `f_bavail` delta is recorded separately from the Tar's logical
size; no host QCOW2 trim or physical host reclamation is claimed.

The guest receipt is
`/var/log/toddy/phase2/h10-selected-tar-custody-1.json`. Host private output retains
`selected-root.tar.gz`, `guest-export.json`, `guest-retired.json`, `export.log`
the immutable `host-verified.json` whose SHA is sent to the guest, and the
evolving durable `result.json`. The original evidence directory and
all its other files remain. Accepted B02/foundation backing files, source/native
package archives, logs, published ISOs, Phase 2 caches and both retained H11
SquashFS copies are outside this profile.

## Failure and recovery

Any partial host context or existing guest receipt stops automatic continuation;
never rerun custody as a retry. If a retirement reply is lost, first read the
fixed guest helper's `receipt` action under the same owned candidate/lock checks.
Compare the actual fixed Tar pathname and custody state before choosing any next
operation. A retained partial archive is not a successful backup.

Recovery requires checking the private gzip's recorded SHA and streaming its
complete decompression into a **new**, reviewed absent guest temporary file.
Verify the original 3,731,302,400-byte SHA before atomically restoring only the
absent fixed Tar pathname; restore mode/UID/GID/mtime/xattrs from the durable
original metadata. Do not extract Tar members, overwrite another path or
replay retirement. Preserved accepted backing images provide independent
historical recovery as well.

Source fixture tests exercise full opaque compression/decompression equality,
truncation/corruption refusal, fixed command selection, durable-intent ordering,
source drift and exact single-file retirement in temporary fixtures. They are
not evidence that the actual candidate file has been exported or removed.

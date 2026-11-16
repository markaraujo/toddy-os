# Protected qualification-only Qwen input

The legacy LFS source cache is intentionally not a protected runtime ancestry.
Do not chmod it or weaken `owned_regular`. The fixed helper copies the already
selected Qwen3-1.7B-Q8_0 model and Apache-2.0 license after full frozen hash and
stable opened-FD verification. It performs no download, activation, package
installation or ISO inclusion. This is explicit development qualification input,
not a product model installation or new acquisition consent.

Before coordinator dispatch, run on the physical host from the checked-out source:

```sh
python3 scripts/build/phase2/qwen_qualification_custody.py host-check
```

This requires host free space >=100 GiB +512 MiB +1,834,437,560 bytes.
The guest cannot observe host capacity; the coordinator must run this host check
immediately before the bounded copy, while retaining exclusive VM ownership.
The model is copied inside the candidate, so an extra full model-sized overlay
allocation is admitted without assuming compression or sparse savings.

After verified source sync, the sole coordinator runs as root in the designated
builder (not inside `/mnt/lfs`):

```sh
python3 /opt/toddy-build/scripts/build/phase2/qwen_qualification_custody.py copy
```

The helper runs `guard_target`, acquires the canonical global build lock, rejects
unresolved native transactions, and requires target free space >=16 GiB +512 MiB
+the same full copy bound. Source paths are fixed:

- `/mnt/lfs/sources/phase2/inputs/local-model-proof/model.gguf`
- `/mnt/lfs/sources/qwen-LICENSE`

Source FDs use `O_NOFOLLOW|O_NOATIME`, root-owned single-link regular files,
exact size/SHA and stable device/inode/mode/UID/GID/ns times. Legacy 0644/0664
modes are accepted only for these hash-bound inputs, never for output ancestry.
Protected output ancestors must be root-owned without group/other write. Newly
created directories are0755; copied files are0444, independently rehashed and
fsynced. All original source bytes/metadata remain unchanged.

Pass these paths to the existing assistant collector:

```text
--model-path /usr/share/toddy/models/qualification-qwen3-1.7b-1/model.gguf
--license-path /usr/share/doc/toddy-native-qwen3-1.7b-qualification-1/LICENSE
```

The durable root-private receipt is
`/var/log/toddy/phase2/qwen3-1.7b-qualification-custody-1.json`.
Only `state=frozen-qualification-copy-verified` reports completed byte custody;
it proves no inference, GUI or product acceptance. Existing destination namespaces,
receipt or `.part` refuse replay. An interrupted intent/partial copy is retained
for inspection; do not delete it or rerun automatically. No source cache is retired.

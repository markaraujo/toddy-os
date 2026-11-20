# Disposable native live Dconf verification

The generation8 observer failure showed that `dconf read` initializes user runtime
state even when the requested setting is a read. Never run this command directly
inside a writable finalized image. Do not repair that historical image or replace
its original snapshot.

The fixed generation9 helper is builder-side:

```sh
/usr/bin/python3 -I /opt/toddy-build/scripts/build/phase2/verify_live_dconf.py
```

It takes no path, action or executable arguments. The coordinator must invoke it
through the protected namespace in `image_native.sh`, using its existing FD9
exclusive build lease. The wrapper's fixed `verify-mvp-live-dconf` action must
route to this builder-side command, not through the target chroot. The target
guard, absent native jobs and private mount namespace remain prerequisites.

The helper requires generation9's actual successful live receipt, nine real
finalizer reports, their source/hash custody and the complete final assembly
snapshot. It binds its own helper hash alongside the other source inputs. It verifies the
current root inode, native Dconf binary, database
root:root mode0644 and content hash, exact session source and attributed user
profile before native execution. Generation8, another root or stale receipts
cannot select the observer input.

A fresh128MiB tmpfs holds a read-only bind of the preserved image, overlay upper,
work directory and disposable merged view. Actual `findmnt` filesystem/options
readback must show a read-only ext4 lower with the same image inode/device, and
a writable overlay with the exact lower/upper/work paths and nosuid/nodev flags.
Only that merged view enters the
native chroot for the three fixed queries. Root user runtime files such as
`run/user/0/dconf/user` therefore belong to the upper tree and are reported in its
bounded inventory. The native process receives a cleared environment and a
30second timeout per query. No source recipe, final snapshot or image file is
written.

The helper checks exact mount identities before strict cleanup and compares the
complete lower image namespace, bytes, metadata, nanosecond mtimes, xattrs and
hardlink classes plus input hashes before and after the session. A failed query
also performs the final lower/input check. An unexpected lower change is a
failure; it never triggers a new snapshot or automatic restoration. The JSON
receipt is printed only after all queries, cleanup and lower comparisons pass.
It explicitly carries no ISO, boot, login, release or G2 acceptance.

The focused filesystem tests use unprivileged disposable copies and simulated
native side effects. They verify the observer boundary and failure behavior;
they are not actual Linux overlay mounts, native Dconf execution or VM evidence.
The coordinator must still execute this fixed helper on the real finalized
candidate before admitting compression.

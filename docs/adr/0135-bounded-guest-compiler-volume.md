# ADR-0135: Bounded compiler scratch in the disposable builder VM

- Date: 2026-11-08
- Status: Accepted; first GTK volume preparation verified

After qualified Rust/SVG prerequisites, the target filesystem has about16.7GiB
free. Preserve its16GiB reserve and existing sources/tests/recovery evidence.
GTK compilation needs additional scratch, while the disposable builder root has
about25GiB free. Both remain overlays inside the authorized isolated KVM guest.

Use one3GiB ext4 regular-file volume in /var/lib/toddy/phase2-scratch on that
builder root, mounted at the already designated empty GTK work directory. This
bounds new host allocation without expanding or repartitioning any virtual or
physical disk. Preflight host free space above100GiB plus the complete3GiB volume
and256MiB margin before preparation. No host installation or new paid resource.

Guest guard, exclusive build lock, absent receipt/image, exact empty mount path,
regular file type/size, generated UUID, filesystem label, actual loop backing and
mount postconditions are required. Write planned/created/formatted/mounted receipts
before advancing. Never replay formatting or uncertain provisioning. The image
is private0600; the work filesystem belongs to the existing unprivileged compiler
UID101 and is mounted nosuid,nodev. The existing read-only-input/compiler sandbox
and one-writer protocol are unchanged. Native installation still uses only the
guarded target root and full verification.

Retain the image and its logs/tests/stage. After reboot, inspect UUID/backing and
mount state before remounting the same image; never recreate it to resume a build.
Its full3GiB capacity is a hard upper bound, not evidence that a build fits or
passes. Account separately for target source/runtime/staging and final-image
space. Other builds require their own measured budget, not automatic allocation.

Actual preparation completed0: regular3GiB image, expected filesystem UUID and loop
backing, mounted nosuid,nodev at the GTK work path with UID101. No physical disk or
target partition change. Native GTK build began in that isolated volume; build/GUI
acceptance remains pending. See [actual receipt](../evidence/B02-gtk-build-volume.json).

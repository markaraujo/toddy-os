# ADR-0221: Read-only native cache transport and the focused Nautilus gate

Status: accepted
Date: 2026-11-11
Scope: B02 development cache custody and disposable native tests

## Context

The isolated Nautilus50.2.2 compiler/stage passed with277ELFs and154staged files.
Its source/compiler/stage lives on the existing2GiB boot-scoped tmpfs. Stopping
the builder loses those aliases. Generation1 cache custody does not include
Nautilus or the later GTK11 schema promotion. Native tests must consume the real
compiled bytes and use the already qualified normal GDM/PAM Wayland user seat.
A source/build checkpoint or mockup is not a native graphical test.

## Verified generation2 custody

Parameterize the existing custody/recovery tools with a strict generation choice,
preserving completed generation1 and its receipts. Generation2 must verify all
prior regular files, metadata and hardlink equivalence classes unchanged, apart
from previously omitted stale sockets. Capture the actual current boot and exact
mount topology. Hold the single guest writer lock while inventorying/archiving.

Generation2 is405,110,654bytes, SHA256
89add46aea68181669f8aa88ad5bb3ef32985cdb87661ec37b92bfc76e48cfaa.
All80,561entries and35,017hardlinks were verified. Actual isolated restoration
passed all content/mode/owner/nanosecond-time/symlink/hardlink checks, with37,820
distinct regular inodes. Prior-generation data remained unchanged. No source,
compiler, fixture, native package or accepted test was replayed.

## Compact native inputs

Create a separate compact archive of only the exact Nautilus source/worker
subtrees. Verify every1904archive entries against the frozen live manifest under
the guest lock. Retain source/compile/stage maps and the original24program
inventory in a root-owned descriptor. No builder/target disk is copied.

The compact gzip is38,945,901bytes. Pad a separate copy with zero bytes to a512-byte
boundary for an explicit raw QEMU data device,38,946,304bytes. Record both full
hashes and lengths. Bind the host input directory read-only and require the QEMU
drive to be read-only with exact serial `TODDY-NAUTILUS-INPUT`. This is a data
image, not a boot disk, installer or published operating-system ISO.

Before creating a test user or starting GDM, the native probe must verify that
serial, block-device type, read-only state, geometry, raw/archive hashes and zero
padding. Restore only into a private384MiB tmpfs, verify every file/metadata/link
class, then expose exact source/work aliases plus `/src` and `/build` read-only.
The native root disk is a fresh disposable overlay over a stopped unchanged
builder target. No physical disk operation, host installation or global device
permission change is involved.

## Focused native tests

Select12original programs covering metadata validation, bookmarks, files,
metadata, copy/rename/trash, Unicode filenames, local search, asynchronous
loading, creation and the LocalSearch-backed files view. Keep all24compiled
programs/inventory. The other12remain unexecuted owner-use coverage, not passes.
No original test is modified and no dependency or sandbox is bypassed.

Use a normal GDM/PAM synthetic user login with private in-memory credentials and
real virtual keyboard/pointer input, as previously qualified. Run selected tests
as that user with NNP/zero effective and permitted capabilities, a fresh private
home per program, the actual Wayland/user-bus sockets and original Meson test
environment. Test-only memory settings/accessibility/renderer flags are upstream
fixture settings, not production preferences or installed-GUI evidence.

Require actual terminal exit0, no timeout, and complete non-skipped GLib test
plans/cases. AppStream is a separate process-based metadata validator. The
original asynchronous-directory driver has no GLib test plan: its exact source
quits the loop only after printing `done loading`. Require that callback marker,
its original default URI and actual exit0, and do not invent a GLib case count.
Per-program observation is bounded to60seconds and the selected run to300seconds;
a timeout is a failure. Preserve the first failure and leave the rest unrun.

Reuse exact input hashes and the proven dedicated-UART report protocol. Assert
source/compiler/stage maps unchanged after execution. Passing this gate does not
prove installed Nautilus, final UI interactions, Gvfs/mounting, full B02 or
physical hardware. Package promotion and real installed Files UI remain separate.

## Observed first native run and collector-only correction

Native attempt1 verified the read-only data device/restoration, normal GDM/PAM
user session and unprivileged controls. Eight selected programs passed, including
59GLib cases. The ninth process also exited0 and emitted three expected unique
search-hit URIs followed by its finished callback. The collector incorrectly
required a TAP plan and stopped before the last three programs. Preserve the raw
failed aggregate; this is a collector failure, not a passing complete gate.

The exact50.2.2 `test-nautilus-search-engine-simple.c` is a non-TAP callback
driver. It asserts total_hits==3 after its main loop. A separate qualification
checks the actual report SHA, original source hash/assertion, three expected
unique basenames, completion marker, exit0 and absence of timeout. It preserves
all59existing GLib cases and validates the successful search process without
rerunning any of these nine programs. A fresh native followup may execute only
the remaining asynchronous-directory/create/files-view programs with the same
exact source/compiler/stage and unchanged base image. Combine both evidence sets
explicitly; do not rewrite the first raw report or invent TAP case counts.

Use the absolute path of the actual authenticated user's Wayland socket. The
installed LocalSearch3.11.1 test-sandbox wrapper changes XDG_RUNTIME_DIR to its
private store/run directory and does not rewrite WAYLAND_DISPLAY. An absolute
name preserves the same real compositor endpoint across that original fixture
environment change. This does not add a display backend, disable sandboxing or
change any original test or production user preference.

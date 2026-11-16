# ADR-0250: Reuse the qualified MVP root through atomic adoption

Status: accepted for the owner-authorized basic MVP only, 2026-11-16.

The owner prioritizes a usable basic-tested MVP in ADR-0249. The original image
pipeline unpacks a candidate, generates/reviews resources, then unpacks a second
root to reproduce that result. The coordinator explicitly authorized waiving only
this independent fresh-second-root reproduction for the typed
`phase2-mvp-preinstalled-v1` class with `g2_eligible: false`. Standard/G2 retains its
existing independent second root and unchanged native runtime/installer code.

Explicit `adopt-finalize-mvp-base` and `adopt-finalize-mvp-live` actions validate
signed inputs, native unpack/database logs, current zero-blocker resource receipts,
independently reviewed maps and the complete current image before mutation. A
new durable intent records source inode, input/source/journal hashes and the fixed
destination. An atomic same-filesystem rename moves the actual root inode into
the existing reviewed-root namespace; parent directories are fsynced. Original
journals remain immutable, with separate adoption and blocked-state receipts.

Only eight fixed synthetic outputs may be reset after exact byte/hash, mode,
UID/GID, same-device, nlink1, origin and non-package-owned verification: the seven
locked policy account files and `/etc/ld.so.cache`, additionally bound to the
actual native loader receipt. No real credentials, owner state or package-owned
file may be removed. The unchanged NativeFinalizer recreates these outputs and
executes all nine real checks, including native caches, private-state, linkage,
whole-image and recovery artifact checks. Independent report/whole-image/input
readback remains mandatory. No success-shaped receipt replaces a native check.

Planned adoption is explicit in the actual first-unpack intent. Only typed MVP
first candidates may reserve one measured root budget, including the offline
bundle, plus the unchanged 16GiB floor and 512MiB margin. Adoption allocates no
second root and still requires that floor/margin. Legacy fresh finalization keeps
its three-copy admission and cannot inherit the one-copy budget.

A partial move/reset/finalizer remains blocked with preserved intents and paths;
there is no automatic replay, rollback or resume flag. Actual ISO installation,
owner setup and two detached UEFI boots/settings persistence still require their
own evidence. The waiver does not complete any story/G2 or claim reproducibility,
BIOS/recovery-mode testing, stable status or physical-machine validation.

# ADR 0248: Trusted first live install and ephemeral fixture credential

- Status: accepted
- Date: 2026-11-16

## Context

The first detached installed boot cannot already exist before its blank target
is installed. The production composition factory correctly requires independently
retained boot/finalizer qualification and remains unavailable until those proofs
exist. The existing root-only installer_qualification source harness uses the
real Installer, LinuxDisk, signed PreparedPayload, NativeFinalizer, fresh owner
and PendingStore callbacks; it deliberately does not grant production readiness.
It lacked a concrete live-ISO/blank-disk controller and protected evidence bridge.

## Decision

Use a source-only coordinator-owned disposable QEMU controller. It accepts an
actual measured live ISO and a deterministic read-only auxiliary ISO containing
only exact reviewed source and prepared native inputs. Every staged runtime
module must match the actual live-installed installer/assistant package payload
and source-manifest pins. Qualification helpers are separately reviewed source,
never an extra production callback, path override or factory readiness flag.

A public firmware/systemd test credential starts a fixed root qualification unit
inside that VM. It preserves the normal fresh toddy-live GNOME session and
installed live-only authority; there is no root autologin, generic pkexec grant,
PAM change, network or global display permission weakening. The unit mounts only
the auxiliary ISO read-only in its private mount namespace, then binds the exact
source/payload to the existing harness paths. The only writable host disk is a
new self-contained64GiB qcow2, serialTODDY-INSTALL-P2-1. The root coordinator must
inspect the actual probed target/plan and explicitly supply its exact SHA before
execution. Passwords use a private same-owner channel and protected pipe; plans
use0600 sealed memfds. Stop requests use the existing cancellation pipe and
canonical journal, not replay or rollback claims.

Preserve actual consistent journal snapshots, the nine original finalizer reports
and actual collector handoff. A read-only collector stream performs the same
existing verification without allocating a16GiB native staging output in the
live RAM overlay. Its host custody retains the unchanged100GiB+512MiB reserve;
the existing native file collector retains its unchanged16GiB reserve. No tmpfs
quota inflation or lowered capacity gate is introduced. Detached boot requires
a successful poststop cold receipt, source disk digest/identity and all reports;
a saved handoff from an interrupted or failed VM alone is insufficient.

For autonomous disposable qualification only, an explicit generated synthetic
owner password may remain in the trusted host controller's RAM. A bounded private
same-UID socket can type it into an exact owned installed-boot context; it never
returns or logs it. Typing requires fresh matching guest boot/round/root UUID,
no active owner/completed desktop, actual GDM greeter plus password PAM worker or
foreground noecho TTY login, and a freshly inspected frame hash. Each round has
one intended typing attempt; an uncertain acknowledgement never triggers retry.
Normal PAM and GDM authenticate normally. A real installation still chooses its
own password. Expiry/death/closure honestly makes the fixture credential
unavailable; there is no silent password reset or claimed login success.

## Consequences

Only actual native execution can establish install/boot/login/cancel acceptance.
Source fixtures never do so. Ordinary cancel waits for the actual terminal
journal/child result before finish. An emergency host/transport/capacity shutdown
may interrupt a native command and is recorded as uncertain, requiring manual
postcondition reconciliation; it never proves safe-boundary completion or undo.
The controller closes the writer VM and detaches both media before cold handoff.
The RAM credential service releases the guest-writer lock before detached boots.
Existing production factory, package/Polkit policy and B13/G2 gates remain intact.

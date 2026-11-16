# ADR-0236: Fixed Calamares native installer boundary

Status: Accepted for source integration; native launch and install qualification pending

## Context

B12 reuses frozen Calamares 3.4.3. Its public C++ ViewStep/Job API supports a
QtWidgets project module without QML/PySide or a framework replacement. Existing
B01 evidence is an offscreen probe, not a graphical or disk installation test.
A composed payload and native image finalizer are still unqualified.

## Decision

Use the fixed project view/job and sealed descriptor boundary described in
[runtime documentation](../../runtime/installer/calamares/README.md). The real
existing Installer retains ownership of disk identity, serialization, account,
boot, hygiene, cleanup and no-replay checks. Only an installed root-owned factory
may provide actual PreparedPayload/boot/PendingStore callbacks. The default factory
fails before any journal or native disk operation until retained native qualification
binds the actual signed payload/catalog, finalizer source and supported firmware.
Candidate JSON cannot provide a path, command, callback or qualification override.

A separate private pipe carries the login password; plan/review/log/GlobalStorage
never contain it. No provider key is collected. The shared deferred setup handoff
must be created as the installed owner and independently pass existing backend
ownership/permission/hash checks.

Disable generic Calamares Cancel during exec: reviewed 3.4.3 ViewManager exits the
application and JobQueue may terminate its job thread. A dedicated modeless Stop
dialog requests the backend's safe boundary and waits; UI loss/control EOF/signals
request Stop without killing a healthy disk command. An uncertain operation remains
journaled for manual reconciliation, never replayed by a second submission.

Upstream expects root Calamares through fixed Polkit/pkexec launch. Actual root GUI
access under GNOME/Wayland is a native gate, as is the missing qualified matching
QtWayland/raster closure (current QtBase probe disables XCB). Do not weaken global
display permissions, inherit owner secrets/session buses, silently switch architecture
or treat offscreen output as graphical proof.

## Evidence and consequences

The source review used Calamares 3.4.3 archive SHA-256
`144cbbf6bdcebfb21685950db4f0777218519df095f62f4aa392f28348110d18`.
Focused fixtures exercise actual Installer plan-only/pre-write Stop paths and
sealedFD/parent identity/readiness/credential guards without native disk calls.
The C++ module has not been compiled/loaded natively. B12/G2 remain unaccepted;
actual signed closure, root GUI, approved scenes, BIOS/UEFI install/Stop/rescue and
media-detached persistent boots are still required. See
[source evidence](../evidence/B12-calamares-source-adapter.json).

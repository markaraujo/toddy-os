# Calamares 3.4.3 source integration

This is an original QtWidgets view module and job for the frozen Calamares
3.4.3 public C++ API. It is preparatory source, not an installed installer or
B12 acceptance. No QML, PySide, shell job, downloaded plugin or replacement
framework is required. The approved brand assets remain unchanged.

`ToddyViewStep` reviews the exact target serial, size, partition plan, firmware,
account, locale, timezone and deferred optional choices. A changed input invalidates
the review; stale asynchronous replies cannot restore it. The password is separate
from the plan and Calamares GlobalStorage. It is captured into a private pipe on
leaving the confirmed page, then removed from the widgets. Temporary Qt/password
buffers have bounded lifetime, not a forensic memory-erasure guarantee. Core dumps
are disabled before password entry. This password creates the fresh installed
owner; API/provider credentials are never requested.

The job starts only `/usr/bin/python3 -I` and the fixed root-owned installed
`/usr/lib/toddy/installer/calamares/cli.py`. Options, reviewed plan and confirmation
use owned, mode-0600 anonymous sealed descriptors. Password and Stop use separate
read-only pipe descriptors. Only descriptor numbers enter argv. Confirmation binds
the immutable plan hash and serial to the actual root Calamares parent PID,
process start ticks, boot ID and ten-minute monotonic expiry. Root is already an
unrestricted administrator; this authenticates a fixed launch path, not a sandbox
against hostile root. The backend environment contains only fixed PATH/HOME/LANG;
it does not inherit the owner's session bus, keyring, tokens, proxies or loaders.

The Python adapter calls the existing `Installer` and the trusted binding object's
actual `PreparedPayload.verify_payload/install_payload`, boot and pending callbacks.
There is no whole-root copy, JSON callback/path/hook selection or dummy completion.
The fixed `toddy.installer.live_bindings.create()` now implements production
composition/source/signature/native-receipt checks and real callbacks described in
[COMPOSITION.md](../COMPOSITION.md). The currently missing qualified composition
still returns `installer_composed_closure_unavailable` before creating an operation
journal or performing a disk operation. Callable presence or a JSON verified
marker cannot replace qualification. No environment/path/hook override exists. Its readiness report fields are `verified`,
`payload_manifest_sha256`, `catalog_sha256`, `finalizer_source_sha256`,
`native_qualification_report_sha256`, and `supported_firmware`.

`save_pending(target, plan)` must execute the existing shared PendingStore as the
fresh installed UID/GID, with the installed user's environment and private directory,
not root-owned JSON copied into their home. The existing backend independently
checks ownership, permissions and handoff hashes. Only non-secret AI/API/local/later
intent and Docker/OpenCode/VS Code selections are deferred. No acquisition or key
collection occurs in the installer. Firmware/account/identity/initramfs/GRUB/hygiene
postconditions remain the actual backend's responsibility; the final page explicitly
leaves installed boot validation pending.

## Cancellation and recovery

Calamares 3.4.3's generic Cancel exits the application; its JobQueue destructor can
terminate a running job thread. Therefore the fixed settings disable that button
during exec. An independent modeless Stop dialog only writes the cancellation pipe
and waits for a safe boundary. It does not exit Calamares, kill its disk writer or
invent completion. Closing the dialog or Escape requests Stop without hiding it.
Before exec, ordinary Cancel remains available. Lost UI control EOF, broken output
or termination signals request the same backend safe boundary. There is no
parent-death kill or write-command timeout in this adapter. An OS shutdown/SIGKILL
may still interrupt a write; the canonical journal requires reconciliation and the
UI reports rescue instead of retrying. Native power-loss/Stop qualification remains
required. The job accepts success only from exit zero plus the exact operation's
completed backend result after its actual cleanup.

## Native build and launch gate

The retained source is `.local/sources/calamares-3.4.3.tar.gz`, SHA-256
`144cbbf6bdcebfb21685950db4f0777218519df095f62f4aa392f28348110d18`.
The API review covers `ViewStep.h`, `Job.h`, `PluginFactory.h`,
`CalamaresConfig.cmake.in`, `CalamaresAddPlugin.cmake`, the default settings,
`ViewManager.cpp`, `JobQueue.cpp`, `calamares.desktop`, the Polkit policy and
welcome `GeneralRequirements.cpp`. The existing B01 offscreen probe is not a
native graphical or disk-install test. CMake requires the exact Calamares 3.4.3
and Qt 6.11.2 inputs. The module has not yet been built or loaded natively.

Upstream launches `pkexec calamares`; its root requirement is implemented by
welcome/GeneralRequirements. Our custom module sequence does not assume that an
omitted welcome module enforces root. The fixed authenticated Toddy launcher and
Python CLI independently require real/effective UID zero. This integration expects
a root GUI and does not replace it with an unprivileged GUI/root helper or use an
upstream test/debug bypass. The existing QtBase probe
recipe disables XCB, and the frozen closure has no qualified QtWayland module.
The coordinator must qualify the matching Qt 6.11.2 raster Wayland QPA closure and
measure authenticated Calamares launch in the actual GNOME session before enabling
an installer desktop entry. Offscreen output is insufficient.

A qualified live-only launch must preserve only the minimum measured display
transport, scrub the owner credential/session/provider/loader environment, and keep
the fixed executable and plugin/config paths root-owned. Never use `xhost +`, weaken
Wayland socket permissions, copy owner keyrings, or enable a broad Polkit action.
If root display access fails, record the concrete native failure and review a narrow
source-backed launcher/authentication change. Do not silently change framework or
version. Exact plugin packaging, display launch, actual EN/PT visuals/scale, approved
slideshow assets, signed composed closure/finalizer qualification, BIOS/UEFI blank
virtual disks, safe Stop and two detached-media boots remain pending. No host or
guest disk was modified by the source tests.

The live-only native package/compile/launch wrappers and explicit first-VM
qualification path are documented in
[scripts/build/phase2/installer-package.md](../../../scripts/build/phase2/installer-package.md).
The module ABI probe is a standalone no-write Qt consumer, not an upstream
nonroot startup/test bypass or a root Wayland result.

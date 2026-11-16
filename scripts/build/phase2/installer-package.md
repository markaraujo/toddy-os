# Live-only Toddy installer package and first native qualification

This source adds an actual native-module staging path and fixed authenticated
launch flow for the frozen Calamares 3.4.3 / Qt 6.11.2 stack. No compiled module,
root GNOME/Wayland launch, signed live composition, disk installation or boot was
produced by the host source tests. Missing native artifacts are blockers. There
is no dummy shared library, fabricated compile/GUI receipt or factory bypass.

The reviewed upstream source is calamares-3.4.3.tar.gz, SHA256
144cbbf6bdcebfb21685950db4f0777218519df095f62f4aa392f28348110d18.
The interface review reads CalamaresConfig.cmake.in, the exported
Calamares::calamares/calamaresui targets, ViewStep.h, Job.h, PluginFactory.h,
Module.cpp, main.cpp and CalamaresApplication.cpp. Header/CMake exports are
installed independently of INSTALL_CONFIG; the accepted upstream probe package
can remain unchanged. The custom module uses its own config tree and module path,
not an overwrite of upstream settings or an upstream module rebuild.

## Ownership and legal split

`installer_package.py` stages only `toddy-installer`, architecture amd64,
version0.2.0-1+toddy1, live-only/offline_base=false. It requires an actual ELF64
x86-64 shared module, no build RPATH/RUNPATH, the expected Qt plugin exports/IID,
real Calamares/Qt dynamic providers and a bounded compile receipt binding the
exact CMake/C++ inputs and successful native no-write ABI consumer. Missing,
non-native or changed artifacts are refused before creating the package stage.

The package owns its Python installer callbacks, unchanged copied offline_payload
and H10 runtime/newc/ELF helpers, one own compiled QtWidgets module, EN/PT strings,
private configuration trees, fixed user/root launchers, a narrow Polkit action,
hidden installer desktop entry and source/legal manifests. It does not own or
modify the Calamares executable/libraries, `/etc/calamares`, the assistant root
namespace, installer handoff helper, upstream Qt files or branding package paths.
`calamares-branding-toddy` owns the unchanged approved logo/scenes and real B02 vs
concept notices. The module/data package declares that dependency. Calamares -c
changes appDataDir and branding lookup, so each own config tree has one exact
relative dependency alias to `/usr/share/calamares/branding/toddy`; assets are not
copied or redesigned. Package-specific stage checks permit only those two aliases;
this is not a relaxation of generic stage symlink policy.

Original code remains MIT and copy/documentation CC BY4.0. The linked Calamares
module is distributed as a GPL-3.0-or-later combined work. The package retains
these terms and references the exact separate Qt/Calamares native source/notices.
Standard stage_package.py retains actual upstream notices from the frozen archive
and records the complete final native archive payload. There are no maintainer
scripts, credentials, private signing keys, model/agent/executor closures, caches,
live accounts or generated production qualification/composition data in this
package. The installed base gets only the separate assistant's canonical
`setup/installer_handoff.py`; the full installer/Qt tree remains live-only.

## Native prepare/build/install sequence

The coordinator runs these only in the designated candidate builder after the
same-version QtBase6.11.2 raster upgrade passes. Existing accepted B02/G1 snapshots
remain preserved. The source wrappers require guard_target, exact actual native
Calamares/Qt package records/archive hashes, the qualified read-only-input UID101
harness, fresh input/work generations and at least the16GiB free-space floor plus
measured staging/archive headroom. Preparation writes only explicit public source
inputs; it does not copy a builder root or run a disk command.

```sh
bash /opt/toddy-build/scripts/build/phase2/installer_prepare.sh
python3 /opt/toddy-build/scripts/build/phase2/job.py \
  toddy-installer-build-2 \
  /mnt/lfs/sources/phase2/inputs/toddy-installer-0.2.0-2 \
  /mnt/lfs/sources/phase2/work/toddy-installer-2 \
  bash /src/installer_build.sh
python3 /opt/toddy-build/scripts/build/phase2/installer_native.py qualify
python3 /opt/toddy-build/scripts/build/run_step.py \
  b12-toddy-installer-2 \
  /opt/toddy-build/scripts/build/phase2/installer_install.sh \
  /opt/toddy-build/scripts/build/phase2/installer_check.sh --user root
```

These are command shapes for the existing coordinator, not commands that ran in
this source slice. Existing files/job receipts/running markers cause refusal;
inspect/reconcile them before any continuation. No uncertain native write is
retried. The wrappers invoke CMake with exact Calamares 3.4.3 and Qt 6.11.2, build
only the own module/no-write probe, reject temporary loader paths and use the
actual native QPluginLoader/factory/widget consumer under offscreen QPA. That
probe does not call onActivate/jobs/exec, query targets, request a password, run
Calamares --test, or qualify the root GUI. Its output has disk_writes=false.

Before promotion, the root wrapper independently checks all staged bytes against
the current explicit source plan, exact declared dependency aliases, the actual
compiled module/receipt, completed isolated job/exit, unchanged native dependency
records and unambiguous direct ELF provider ownership. The source manifest is not
accepted as its own authority. Promotion preserves source/asset/legal hashes and
uses the existing native package manager/ownership checks and run_step recipe plus
postcondition boundary. Postcheck verifies configured package/source/module bytes
and an actual installed module ABI consumer. It keeps root Wayland/disk boot
qualification pending and does not launch a GUI or reset user settings.

## Fixed owner authentication and root Wayland gate

`/usr/bin/toddy-installer` sends only a bounded display name and EN/PT locale to
`pkexec /usr/libexec/toddy-installer-auth`. Its distinct Polkit action uses
active-only auth_admin, no remembered authorization, arbitrary command or broad
GUI-environment preservation. The root entry runs isolated Python from fixed
/usr/lib and requires real/effective UID0 plus the native PKEXEC_UID identity.

The helper independently queries authoritative system logind for the same UID's
active, local, unlocked user Wayland display. It verifies the canonical owned0700
/run/user/UID directory and real owned socket, then checks actual SO_PEERCRED
without sending Wayland requests. Socket leaf permission bits are not assumed to
be0600: upstream Wayland1.26.0's bind can retain the compositor umask; the private
0700 parent and kernel peer UID provide the required access/identity checks.
No socket/directory permissions are changed, and no xhost/X11 fallback exists.

Only a closed fixed environment reaches the actual `/usr/bin/calamares -c` path:
Wayland transport, selected EN/PT locale, root-private HOME/config/cache/data and
fixed `/usr/plugins` raster QPA paths. The owner session bus, keyring, provider
values, proxies, loaders and import environment are not inherited. Core dumps are
disabled before the UI. The custom sequence does not assume welcome-module root
checks: both the root launcher and Python backend enforce UID0 independently.
No upstream test/debug option bypasses them.

The desktop entry currently has NoDisplay=true. Production launch also requires
an actual root-protected `launch-qualification.json` plus normal signed
composition readiness. The receipt binds the Calamares/module/launch-source/
settings/ENPT-string/Wayland-platform/xdg-shell bytes and measured root GUI,
active owner, no inherited session bus, EN/PT visibility, keyboard focus,100/200
scale and safe pre-write Cancel observations. The package generator emits none
of these observations or a placeholder receipt. Actual measured live-image
promotion must retain and attribute that data and expose the desktop entry only
when the installed fixed launch path has passed. Root GUI/display compatibility
remains unverified until that native probe happens.

## First trusted blank-VM harness: no production chicken-and-egg

`scripts/build/phase2/installer_qualification.py` is a separate root developer
harness. It is not in the native payload, desktop entry, Polkit action or
production factory. There is no production flag/env/path that selects it.
Production create() still requires retained native finalizer and detached-boot
receipts. The harness can collect the first evidence using the actual same
low-level callbacks and an exact QualificationPolicy serial.

First collect/review actual native base composition inputs at the fixed private
`/sources/stage/toddy-installer-native-inputs`: signed prepared payload, reviewed
policy.json, generated-entries.json, measured boot-profile.json and the complete
actual expected-image-manifest.json. These are observed source/ownership/metadata
inputs, not a dirty builder-root copy, guessed report or fake completed image.
The harness rechecks signed archives/custody and hashes, shares the production
fresh-owner namespace guard, builds the actual ext4 initramfs, runs the native
finalizer and invokes canonical PendingStore as the installed UID. Its inputs
object deliberately has no production readiness() report. Unknown image outputs
still fail the independent image audit and require reconciliation; they cannot
be accepted by an unconditional callback.

A root coordinator provides sealed0600 options/plan descriptors and dedicated
private credential/Stop pipes. Options and plans never contain a password. The
review command probes only the explicitly selected blank virtual disk and emits
the exact plan/hash without writing it. Execution requires the same reviewed
hash, explicit TODDY-INSTALL-* serial, real virtual-device identity and the
existing immediate pre-write identity/authorization/cancellation checks. The
journal is separate at /var/lib/toddy/installer-qualification. SIGINT/TERM/HUP or
control EOF request a safe boundary; no writer is killed or replayed.

```text
installer_qualification.py review --options-fd N --serial TODDY-INSTALL-EXACT
installer_qualification.py execute --plan-fd N --credential-fd P --cancel-fd C \
    --serial TODDY-INSTALL-EXACT --confirm ACTUAL-REVIEWED-PLAN-SHA256
```

Descriptor numbers and uppercase placeholders must come from the actual trusted
root harness. They are not commands to replay. Never reuse an uncertain target
or invent a new operation ID to evade its journal. Native failure/Stop, rescue,
installed privacy, fresh login, two detached-media persistent boots per advertised
firmware and failed-update recovery remain required measurements. Actual boot
observations feed the existing sealer/production composition contract, not this
harness's exit status alone.

For first root display inspection before production boot receipts exist, the
same developer tool has `gui --uid ACTUAL-ACTIVE-OWNER --display wayland-N
--locale en_US.UTF-8|pt_BR.UTF-8`. It still requires UID0, authoritative logind,
private transport/peer checks and closed environment. It starts the real
Calamares executable with a fixed **show-only configuration with no exec step**;
there is no Calamares test/debug bypass or disk writer. This can measure the
actual Qt raster/root/GNOME transport and visible states without pretending that
missing production composition is available. Use dummy private login-field text
for visual checks and retain actual screenshots/reports outside the image.

Source checks: `python3 -m unittest discover -s tests -p test_installer_package.py`.
They exercise source-layout imports, missing-artifact refusal, session/socket/peer
and environment guards, recipe identity, direct-provider ownership and stage
manifest custody. They never compile a substitute module, write guest disks,
change host dconf or count a fixture as native GUI/installer acceptance.


## Native module attempt 2: explicit exported dependency

Attempt 1 reached CMake generation and stopped before C++ compilation because
Calamares 3.4.3 exports `KF6::CoreAddons` but its installed config does not discover
that target. Its actual public interfaces are `yamlcpp::yamlcpp`, Qt Core/Network
and KF CoreAddons for libcalamares, and libcalamares plus Qt Core/Gui/Widgets/Svg
for libcalamaresui. The upstream config already discovers Qt/YAMLCPP.

The module now explicitly finds frozen `KF6CoreAddons 6.29.0 EXACT CONFIG` before
Calamares. Native package dependencies and preparation custody include exactly
kcoreaddons 6.29.0-1+toddy1, yaml-cpp 0.9.0-1+toddy1 and qtsvg
6.11.2-1+toddy1 for these public interfaces; no new provider or version is selected.
Calamares and Qt remain the existing installed packages.

Preserve all failed attempt-1 source/work/job/cache/log/receipt paths. Attempt 2
uses source `toddy-installer-0.2.0-2`, work `toddy-installer-2`, stage
`phase2-toddy-installer-2`, prepared receipt `toddy-installer-prepared-2.json`, job
`toddy-installer-build-2`, dispatcher `b12-toddy-installer-2`, native install receipt
`toddy-installer-install-2.json` and offscreen postcheck directory 2. Run the
prepare/build/qualify sequence above with those new names. This is a new own-module
attempt, not a retry of an uncertain native install or an upstream rebuild.
The complete current live-session/generated-resource source closure is retained.

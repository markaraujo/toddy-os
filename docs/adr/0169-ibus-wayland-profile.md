# ADR-0169: IBus with the owned Wayland-only GTK backends

Status: accepted implementation profile; runtime qualification pending.

## Actual source and failure

The frozen IBus1.5.34 archive is SHA256
ff8f511770844203108119727dc8686c29afb286e9cb535e0870f18d40fddbbb.
The frozen BLFS13.1-systemd general/ibus.html page is SHA256
ad41f2c64f8d20e4e97c9968b67de7c733d0cf60bea66fc1e91c30d08c85b724.
Actual configure.ac and client/gtk2/ibusimcontext.c are the implementation sources.
GTK3 and GTK4 use symlinks to this shared C file. The owned GTK backends select
Wayland; presence of libX11 alone does not supply GTK X11 headers or APIs.

Initial job ibus-1 completed autogen/configure, then failed compiling GTK4 because
cursor-coordinate X11 calls were guarded by HAVE_XIM, while their headers use
GDK_WINDOWING_X11. The first targeted correction moved display lookup before
the backend condition and required both defines for the X11 transform. This
preserves the Wayland display reference and existing zero X11 translation offsets.
Both GTK3/GTK4 modules subsequently compiled and linked. Job ibus-gtk4-2 then
failed independently in the optional client/x11 agent, which includes absent
GTK X11 headers. Neither attempt reached original tests or staging.

## Decision and bounded recovery

Select upstream --disable-xim for the minimal GNOME/Wayland profile rather than
rebuilding accepted GTK with an unrequested backend. Keep GTK3/4 input modules,
Wayland, introspection, Unicode dictionary, setup/UI, DConf, systemd support,
notifications and the simple engine. Optional XIM/X11 operation is unqualified.
The shared-source backend condition remains correct independently of this flag.
No claim of X11 desktop compatibility follows from portable library validation.

Source/archive inputs remain immutable. Autogen and book corrections operate
only in a private unprivileged working copy. Reconfigure the changed XIM option
once there and compile affected objects. Retain all three job identities/logs;
never replay preparation/autogen or overwrite failed logs. Seven portable original
drivers are selected initially. Bus/display/uinput/locale-sensitive originals,
actual installed service recovery, module/cache/schema ownership and actual GNOME
keyboard interaction remain required follow-up evidence. No native install or
complete B02 acceptance is established by this profile decision.

The no-XIM configuration compiled the production modules/daemon, but its original
Xlib stress fixture could not link: configure leaves X11_LIBS empty with XIM off,
while bus/test-client.c unconditionally calls Xlib. Override only the original
fixture link variable `test_stress_LDADD=$(AM_LDADD) -lX11` with the existing owned
libX11. No test assertions, production ABI or GTK backend changes. Job ibus-link-4
resumes make without another configure. Building this fixture does not execute
its display-dependent stress test or qualify X11 operation.

## Verified isolated result

The corrected fixture link completed compilation. Five portable originals passed;
only ibus-share failed because the isolated namespace had no machine ID. Extend
the existing exact-input synthetic /etc/machine-id fixture to this IBus input,
without copying real identities. Preserve the six initial logs/results, repeat
only ibus-share, then run test-matchrule for the first time. All seven selected
originals passed,179 compiled artifacts remained unchanged,200 regular staged
files retained, own UTF8 roundtrip/key parser refusal/two-cycle recovery passed.
Job ibus-machine-5 terminal0. No native installation/private-bus/GUI acceptance.

The frozen source tag is1.5.34 but upstream configure/header metadata declares
1.5.34-rc2. Preserve those bytes and disclose the distinction; do not silently
rewrite it or claim a newer release. Native package version mapping is a required
follow-up before promotion. [Build evidence](../evidence/B02-ibus-build.json).

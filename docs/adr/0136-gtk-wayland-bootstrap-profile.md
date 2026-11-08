# ADR-0136: Native Wayland GTK bootstrap and separate graphical acceptance

- Date: 2026-11-08
- Status: Accepted native bootstrap profile; graphical/session/media acceptance pending
- Sources: frozen GTK4.22.4 meson.options/testsuite; ADR0110/Phase2 validation policy

Build the selected GTK4.22.4 against the already owned native image, text,
Wayland/EGL/GL, geometry and keyboard stack. GTK source directly requires TIFF;
its156 native tests and owned image API checks are qualified. ISO Codes4.20.1
provides actual country/language/Portuguese gettext data. This does not enable a
Gdk TIFF loader or change the selected source/runtime versions.

The bootstrap enables Wayland, introspection, demos and compiled tests. X11,
Broadway, Vulkan and optional print/cloud/search/profiling backends are disabled.
GStreamer media is explicitly pending its native dependency chain and must be
qualified before claiming the integrated media experience; it is not a finished
GTK distribution media profile. Keep the native demos for later actual UI QA.

Before a compositor exists, run the original bitset, stringlist and rgba source
test programs: their mains use plain g_test_init and need no display. Record real
TAP cases/exits and reject skips/failures. Add actual C and Gtk/Gdk/Gsk GI API
consumers, including Unicode model content and navy color parsing. Generate the
strict GTK schema cache privately in stage; upstream DESTDIR does not perform
global postinstall generation. Native package ownership/postconditions must be
verified through the full-root runner.

These checks allow bootstrap library promotion needed to build the compositor;
they do not pass B02, native window/focus/navigation/responsiveness, display-based
upstream tests or B11 artwork acceptance. Those remain explicit work against the
actual native Wayland/GNOME session, along with theme/schema/media/service
integration and the essential security/boot/recovery gates. Do not count an
unopened widget, offscreen fixture or HTML concept as graphical acceptance.

Use the bounded guest compiler volume under ADR0135 without altering the existing
sandbox, compiler privileges or installation target. Preserve successful results
and choose only affected checks on subsequent input changes.

Bootstrap build/stage completed0:30 selected upstream cases (15bitset,10stringlist,
5RGBA), real C and Gtk/Gdk/Gsk GI consumers0 and private strict schema cache0.
Actual installation/postcheck is the next gate. Upstream skipped global icon/MIME
updates under DESTDIR; these require controlled integration with their owning
packages after the theme/app set is installed. They are not declared completed.

Owned installation completed0; original postcheck1 queried the GTK3 schema name.
Frozen GTK4 source and actual registry prove the gtk4 namespace. Read-only full
payload/archive guard and corrected postcheck-only recovery0/0; no reinstall or
source/upstream replay. Installed C/GI/schema checks0,2132 legal notices. Keep
original failure evidence. No actual window/session acceptance follows from this.

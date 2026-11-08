# ADR-0130: Real Xorg comparator for keyboard data validation

- Date: 2026-11-08
- Status: Accepted; native headless SDK owned0/0, keyboard data qualified

The minimal Wayland libxkbcommon1.13.2 build passed all26 registered library
drivers. Original xkeyboard-config2.48 data Pytest also invokes the Xorg xkbcomp
compiler (tests/test_xkb_symbols.py). That executable was absent; the original
suite reported failed comparisons and Meson's60s timeout. Preserve that failure,
compiled libraries and stages. A timeout is not acceptance. Do not remove the
upstream comparison merely because the current runtime profile disables X11.

Build pinned xkbcomp1.5.0 and its ten-component headless SDK closure from the
existing BLFS13.1-systemd book. config/phase2/xorg-validation-sdk.lock.json binds
the sources/versions/options. Grouped x7lib/x7app checksum tables select only an
explicit exact archive row; reject missing/ambiguous/path-bearing filenames.
Verify official HTTPS archive against the frozen book checksum, then freeze
SHA256 before extraction. This selects prerequisites, not every Xorg package.

Use qualified UID101/offline/read-only-input isolation, independent stages and a
private cumulative SDK. Relocate only private pkg-config metadata; final stages
retain /usr, no temporary runtime search paths. Remove staged libtool archives,
verify payloads/links/permissions/collisions, retain exact legal notices, and own
each archive independently through the existing full-root native transaction.
Keep libX11 locale/Compose data. Do not install an X server or claim a session,
physical keyboard, actual credential flow or graphical acceptance.

Run registered upstream suites and report actual registration/case results.
libxcb optionally uses the Check framework, absent from the frozen book/target;
its configure explicitly makes that suite conditional. Record those units as
unavailable, never as passed because make check returns0. Require real native
keysym/resource/auth serialization/allocation/display-parser API consumers and
xkbcomp valid/invalid compiler cases. Auth data is a synthetic fixture, unrelated
to product credentials. Then rerun the affected original keyboard data suite
with the real compiler and adequate timeout; reuse unchanged library26 evidence.
No frozen foundation upgrade, full X server matrix or graphical mock acceptance.


Native SDK install/post both0 in38.552s full-root verification. Ten independent
archives and exact retained legal notices are bound in B02-xorg-validation-sdk-
install.json. Real libXau1/libXdmcp1/libxcb check-pc1/libX11 Compose1 tests passed;
Check-based libxcb units registered0 and xorgproto evdev-keysym-check skipped for
missing optional Python libevdev. Header/macro components have no registered
executable suite; downstream native compiler/API consumers passed. Original SDK
job1 exit1 was an empty compatibility-map fixture after C/API success. Corrected
compiler-only recovery2 passed valid0/invalid1 with every stage unchanged. Both
original failure and recovery are retained; no failed result is relabeled0.

With native xkbcomp1.5.0 installed, original keyboard data driver completed0 in
14.72s:5516 passed/3164 upstream skips (optional pycountry ISO-country/language
validation unavailable). All original26 library drivers retained; context and
Compose affected by new locale data rechecked2/2. Actual staged US/BR/PT Shift
and registry consumer0; original compiled/staged payloads unchanged. This is
headless API/data evidence, not native GNOME navigation or physical input proof.

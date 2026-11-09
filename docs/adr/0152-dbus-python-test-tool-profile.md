# ADR0152: D-Bus Python native test-tool profile

Status: accepted for B02 test tooling, 2026-11-09.

The frozen D-Bus Python1.4.0 source offers its supported Meson build directly.
Use that backend and preserve its published dbus_python.egg-info metadata rather
than add a wheel frontend solely for this extension. No source API change or
invented Git metadata is required. Source SHA256 and build/test evidence are in
[B02 installed evidence](../evidence/B02-dbus-python-install.json).

Seven original registered programs passed. The eighth, import-repeatedly,
explicitly returns the exact issue55 TAP skip on Python>=3.12 in the frozen
`test/import-repeatedly.c`. Preserve that skip as an unsupported embedding
profile. The selected test tooling initializes Python once per process; it does
not qualify repeated interpreter destruction/reinitialization.

The initial own all-OK gate refused that skip after compilation, staging and the
private-bus consumer succeeded. A separate verify-only job accepted only the
exact source/version-bound skip and proved all32compiled ELFs unchanged. No
compiler, stage or original suite was replayed. Owned installation and actual
installed typed UID, missing-peer refusal, name lifecycle, reconnection and
Dpkg/APT checks passed. These prove a test dependency, not Polkit authorization,
GNOME login or a complete desktop.

# ADR-0041: Measure native Expat consumers and configuration boundaries

- Date: 2026-11-06
- Status: Initial measured review; complete release exposure review pending

The actual 101-package root has nine dynamic Expat API consumers among 2551
ELFs: four CMake frontends, DBus daemon and activation helper, xmlwf, Libarchive,
and Python pyexpat. Dynamic imports do not enumerate static/bundled parsers,
Python callers or downstream desktop consumers. Repeat against the final image.
Keep ADR-0013's unresolved upstream issue visible; do not claim all Expat
vulnerabilities fixed or reinterpret full library tests as application bounds.

Frozen DBus 1.16.2 bus/activation-helper.c get_correct_parser selects only
DBUS_SYSTEM_CONFIG_FILE in production. TEST_LAUNCH_HELPER_CONFIG is inside
ACTIVATION_LAUNCHER_TEST and is absent from the actual installed helper strings.
The helper remains root:18 mode 4110. The inspected native system.conf is
root:root 0644, configuration directory 0755; H08/image checks must preserve
trusted configuration/include ownership. Do not execute arbitrary test XML
through the privileged helper.

bus/config-loader-expat.c explicitly treats configuration as trusted XML and
sets a fixed hash salt for early-boot availability. dbus/dbus-file-unix.c rejects
regular files above one MiB before parsing. Actual unprivileged UID 101 daemon
probes, with two-second CPU/128 MiB address-space limits and five-second timeout,
rejected syntactically incomplete XML and a 1048577-byte file with expected
native errors (both exit 1). No bus was started. Initial malformed fixture used
an unknown element and was correctly rejected by the semantic validator first;
preserve that failed probe, correct the fixture, and require parser-specific
error in the repeated check. This is bounded config rejection, not proof of
complete CVE mitigation or startup acceptance.

Frozen CMake 4.4.2 Source/cmXMLParser.cxx and Libarchive 3.8.11
archive_read_support_format_xar.c use Expat for file/build/archive inputs.
Their use does not establish safe total decompressed size or wall-clock bounds:
Libarchive's INT_MAX chunk check is not an overall resource budget. Python's
pyexpat exposes a general API, not a universal policy for its callers. Agent,
installer and desktop integration must process untrusted inputs unprivileged
with explicit byte/resource/time limits and tests at their actual entry points.
Never feed untrusted XML into privileged configuration paths as an unblocking
shortcut. xmlwf is an optional user-invoked validator, not an exposed service.

Evidence outside Git:
- .local/logs/h07-expat-consumers-101.json, SHA-256 18fd6166164a66c54a2e64e134d5ce9ab494b7c0d98a9e91eeb5e7477d0de5f5.
- .local/logs/h07-dbus-xml-bounds-101.json, SHA-256 7cc19576a36032fce68537b04fee8f25de333c02be0e2447d9b590ba36b6aa8a.
- .local/logs/h07-dbus-xml-bounds-semantic-fixture-101.json (initial probe).

Reproduce with scripts/build/audit_xml_consumers.py and
scripts/build/audit_dbus_xml_bounds.py in the guarded builder. Source statements
above come from the exact frozen DBus/Libarchive/CMake archives in the committed
source locks, not moving upstream documentation. A new consumer requires review;
this ADR does not close H07/G1 or later desktop exposure requirements.

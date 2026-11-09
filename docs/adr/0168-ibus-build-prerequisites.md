# ADR-0168 — Qualified compiler and Unicode data for IBus

Date: 2026-11-09. Status: verified prerequisites; IBus/runtime GUI still pending.

The frozen BLFS13.1-systemd general/ibus.html selects IBus1.5.34, requires
Vala0.56.19 and additionally installs Unicode17 UCD. Actual IBus tools contain
Vala source, so a real native compiler is required. Do not import a workstation
binary or replace the selected runtime. Build Vala from its exact frozen official
archive with the owned GCC/GLib toolchain and GNU17 for generated C. Omit optional
Valadoc/coverage/sanitizer matrices. All1435 original test programs and enabled
auxiliary make checks passed. Retain282 compiled ELF objects and340 staged files.

The first own staged compiler check could not find its private code-generator
library in /stage/usr/lib/vala-0.56. Correct only that staging search path and run
the unchanged consumer under a new directory; original tests/artifacts/stage stay
unchanged. Actual generated GObject/UTF8/signals/typed-error native code runs,
invalid typed source is rejected without an executable, and a subsequent valid
compilation recovers. Owned native install/post0/0 changed366paths/373entries;
actual installed compiler repeats only this affected consumer and SDK/APT checks.
This is a build SDK, not IBus/keyboard/desktop or mandatory base-image acceptance.

## Versioned Unicode source and complete notices

Use the book's exact official Unicode17 UCD HTTPS URL. All74 ZIP entries/CRCs
and embedded Version17.0.0 marker were checked; SHA256 was frozen before guest
use. No separate publisher checksum or signature is claimed. Full Unicode
License V3 is independently fetched from its official source and its exact bytes
pinned, alongside UCD ReadMe copyright/version. Standard Unicode-3.0 permission
and notices are retained; no account, hosted provider or paid resource is used.

The general tar extractor remains unchanged. A small UCD-only ZIP extractor
validates all paths/types/duplicates/encryption/size/CRC/version before any input
write; symlinks/traversal are rejected and extracted regular data receives no
executable permissions. Three meaningful data-source
safety regressions passed. Notice retention now also handles declared top-level
ZIP legal material and explicitly reviewed plain license sources, preserving
exact bytes in the package. Existing tar/wheel behavior remains covered;12notice
checks pass, including traversal rejection and refusal to treat arbitrary plain
source as legal text. No global security setting is changed.

Actual isolated data staging preserves all71 regular source files. Native data
validation checks40575 ordered Unicode scalar records,346 nonoverlapping block
ranges, UTF8 names and Portuguese/emoji metadata. This is not a Unicode conformance
suite, glyph rendering or input-method test. Native architecture-all package
install/post0/0 changed87paths/85owned entries; actual installed data and both
complete pinned notice materials passed. Retain the source/data evidence without
inventing an upstream executable suite for static data. UCD build data is not
automatically part of the final minimal base-image runtime closure.

Continue IBus using frozen source instructions: GTK3/4/Wayland/GI and Unicode
dictionary; book-selected optional emoji dictionary/appindicator/GTK2/Python2
omitted. Original display/uinput/locale-sensitive tests need explicit scope and
real native validation, never fake passes. Shared GTK3 IM cache and GTK schema
ownership require controlled integration; do not overwrite another package's
cache after installing a module. Existing GTK4 has an exact GTK3 revision pin,
so review/adjust only that control constraint before a GTK3 cache revision.
Actual GNOME login/apps/offline/audio/input and physical hardware remain pending.

[Vala](../evidence/B02-vala-install.json), [Unicode data](../evidence/B02-unicode-ucd-install.json).

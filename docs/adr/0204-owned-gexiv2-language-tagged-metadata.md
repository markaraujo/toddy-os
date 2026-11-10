# ADR-0204 — Owned GExiv2 and language-tagged metadata readback

Status: accepted, native prerequisite qualified; desktop acceptance pending.
Date: 2026-11-10 · Story: B02

Use frozen BLFS13.1-systemd `gnome/gexiv2.html`, GExiv2 0.16.2 official source
SHA256 `aad9e240fdffbe85e390f46ee0a567e251baea5c29c3d8690260388683dc8d0a`.
The source archive matches the frozen book MD5. Reuse owned Exiv2 0.28.8 and
GLib 2.88.3 without changing foundation versions. Build the shared GObject API,
GI, Vala interface, Python override and original tools; documentation generation
is unselected. Preserve component copyright notices through native packaging.

Actual UID101/read-only-input isolated build1 compiled and staged successfully.
All three original registered programs passed: C regression and both Python
modules. The additional own GI consumer then failed: `Xmp.dc.title` is a
language alternative, and the real string includes `lang="x-default"` before
the intact UTF8 value. A read-only query of the already-produced file confirmed
this exact value; there was no evidence of corruption or parser failure.

Correct only the own expectation and run a new private consumer directory.
Probe2 passed two PNG UTF8 metadata write/read/reset cycles, unchanged IHDR,
IDAT and IEND chunks, malformed-JPEG refusal without changing either file, and
two recovery cycles. All 22 compiled ELF and 16 staged regular-file hashes
remained identical. No compilation, original program or staging replay occurred.
The immutable original probe and failure remain in the evidence; the qualifier
binds the exact one-line correction and recorded recovery command.

Native install/postcheck returned 0/0, 32 changed paths and 42 package entries.
The installed UID101 consumer with private devices and no network route passed
the same behavior. Stage bytes, pkg-config, shared Exiv2 linkage and APT checks
passed. [Native proof](../evidence/B02-gexiv2-install.json) includes source,
transaction, package and immutable raw-evidence identities.

This qualifies a metadata prerequisite, not LocalSearch, Nautilus, GNOME login,
graphical interaction or general parser security. Existing Expat limitations
remain. Actual LocalSearch Landlock/seccomp and desktop acceptance are required.
The continuation boundary remains: complete all B02, then stop.

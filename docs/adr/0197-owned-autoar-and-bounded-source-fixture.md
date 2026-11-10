# ADR-0197 — Owned gnome-autoar and a bounded original source fixture

Date: 2026-11-10
Status: Accepted package/userspace slice; actual file-manager GUI pending

Use frozen BLFS13.1-systemd `gnome/gnome-autoar.html`0.4.5, archive SHA256
`838c5306fc38bfaa2f23abe24262f4bf15771e3303fb5dcb74f5b9c7a615dabe`,
book SHA256
`0f05481f579db98cc5d5a80f8fdd57bd344749ba707f99c573218980f043bdbb`.
Select core/GTK3/GI/Vala, original tests, no optional documentation. Reuse actual
owned Libarchive3.8.11-1+toddy1, frozen by ADR0017/supplemental source lock; do
not downgrade to the book comparison3.8.9 or rebuild accepted foundation libraries.
Retain exact LGPL2.1-or-later root and leading runtime C/header notices.

## Source extraction and dispatch correction

First preparation safely refused one absolute symlink in the authenticated
upstream negative fixture. No source/work tree was extracted. My chained command
incorrectly dispatched despite that failure; job1 exited1 at missing realpath,
with no compiler or source/work mutation. Preserve both failures.

Permit only this exact archive/member/type/size0/target:
`tests/files/extract/test-symlink-parent/reference/arextract -> /tmp`, under the
exact `gnome-autoar-0.4.5/` root. Standard data-filter path/permissions/ownership
checks still apply. Whole-archive preflight requires one exact reference, rejects
duplicates/descendants, absolute member paths and parent components **before**
creating any source tree. Other links/archives retain existing rejection rules.
This is test reference data, never a production payload/link or an execution grant.
Ten focused source-filter tests cover existing Dpkg/AppStream rules plus exact
positive/wrong identity/kind/size/target/duplicate/missing/traversal refusals.
Actual frozen178member archive preflight passed. Preparation source-filter2 then
completed0 once. The versioned job controller now rejects missing source/work
before creating dispatch state; actual negative dispatch proved no log/receipt/
compiler creation. Local default leaf launcher also binds the prepared receipt,
recipe SHA and frozen source identity before launching.

## Real tests and recovery

Original automated extraction driver writes output beside its fixtures. Run its
unmodified compiled binary with only G_TEST_SRCDIR selecting a byte/mode/link
identical private130entry fixture copy. All22original cases passed/no skips,
including conflict, symlink-parent, dotdot/absolute containment and encrypted
fixtures. Source and private input/reference bytes unchanged; only designated
output subtrees changed; no `/tmp/arextract.txt` escape. Manual create/extract/UI
programs compile only, not test passes.

The own C consumer initially omitted setlocale, so its UTF8 ZIP filename failed
conversion under C's default ASCII locale despite the environment. Correct only
the consumer to inherit/assert UTF8 locale, and use actual staged
GnomeAutoar/GnomeAutoarGtk0.1 namespaces. Probe3 passed with all19compiledELFs/
21stagefiles unchanged. No original fixture/suite/library/source replay.

Native install/post0/0 changed52paths/57owned entries. Actual installed UID101,
private-device/no-route target userspace passed four Unicode ZIP extractions,
two empty-archive refusals, two pre-cancelled no-destination outcomes, two recovery
cycles, retained unchanged input archives, C/GI/shared ABI/pkg-config/APT0.
No global locale/policy/permission or owner configuration changed. This is builder
VM userspace, not a native desktop/physical test. No all-format, GUI or
mid-extraction Stop acceptance; real Nautilus actions remain required.

[Full source/failure/test/native proof](../evidence/B02-gnome-autoar-install.json).
Native archive SHA256
`756ca997fdaab96b098564b17977b772cc91bdd0260a5466c504c87343e71bf7`;
native raw evidence SHA256
`a5e43471ab29fcf7eb318a9e6f2957c06bf8a8704638a8eb709b0849dd277198`.
Host preparation failures/negative guards have a separate immutable raw bundle
linked in that proof. Run affected filter tests and repository checks; no unchanged
foundation/native original suite is repeated for this narrowly scoped exception.

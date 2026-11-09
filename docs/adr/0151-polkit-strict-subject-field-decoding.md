# ADR-0151: Reject malformed Polkit process identity fields

- Date: 2026-11-09
- Status: Native parser correction verified; full authorization integration pending

Frozen Polkit127 (source SHA256
9b7bc16f086479dcc626c575976568ba4a85d34297a750d8ab3d2e57f6d8b988)
ignores errors from its optional uid lookup. An actual uninstalled native library
accepted both a wrongly typed unsigned uid and duplicate uid keys. A correctly
typed self-process remained accepted. This reproduces decoding behavior behind
[upstream issue701](https://github.com/polkit-org/polkit/issues/701), not an
observed privilege escalation or an installed daemon acceptance.

Apply the explicit one-file patch in config/phase2/polkit-patches.lock.json.
Validate the known process fields uid(i), pid(u), start-time(t), pidfd(h), rejecting
wrong types or duplicates before choosing a representation. Refusal must also
work when the caller does not request a GError. Preserve unknown attributes as
data and the existing absent-uid legacy API; this does not qualify racy legacy
PID input for the owner's privileged executor, whose independently authenticated
peer/owner policy remains mandatory.

The patch also returns immediately after a required-field type error, avoiding
a second GError assignment, and releases the borrowed-value reference acquired
by lookup on the invalid unique-bus-name path. Public headers/signatures and
source version remain unchanged. This is an explicit Toddy downstream correction,
not a claim of an upstream release/fix or complete semantic ABI/security coverage.
Retain original source/library/diagnosis and exact patch/authorship/license data.

A new immutable input copied every original file, then changed only
src/polkit/polkitsubject.c with fuzz0. Original source file SHA256
760e7f8230896e5e54bda8ab88eb85f9e984a7ec8d8671b3ba6ad2f711453bb3;
corrected SHA256f314fad12594bbb42b0e665874c430217938e9e30f40481ca4c190c39985a0f9.
Actual corrected native13cases plus9NULL-error-pointer refusal controls passed
with G_DEBUG=fatal-warnings. Valid subjects/unknown attributes/legacy absence
remained accepted; malformed process/session/bus values failed clearly.
[Original/corrected proof](../evidence/B02-polkit-subject-diagnosis.json).

Both builds are library-only diagnostics, package_promotable=false. Before an
owned Polkit runtime require the original full suite on native namespaces, actual
system-bus/privilege/credential/cancel/recovery checks and the affected graphical
permission flow. Python D-Bus1.4.0 and DBusMock0.38.1 are pinned test prerequisites;
fixtures remain distinguished from real account/authorization tests. Do not mark
B04, GNOME or B02 complete from a parser result.

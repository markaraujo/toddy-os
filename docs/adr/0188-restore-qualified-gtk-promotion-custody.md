# ADR-0188: Restore-qualified custody of duplicate GTK promotion stages

Status: eight actual archive restores verified; duplicate promotions retired.

Target available space was17386262528bytes, near the16GiB reserve. Before new
application builds, recover only eight explicit GTK4 promotion replicas (native
revisions toddy1–8). Do not remove original source,
compiler stages/tests, installed GTK, native archives or package records. Do not
replay older custody/trim operations or touch physical host disks.

The existing source/target guard and exclusive guest writer lock are required.
Match each exact current stage payload/modes/owners to its retained native record,
verify archive SHA and Package/Version, stage inode and absence of nested mounts.
Restore EACH archive to a NEW temporary stage, verify every restored data entry
and control file bytes/modes/owners against the original stage/record. Respect the
16GiB reserve during each restoration. Only after all eight restores pass, remove
only usr/etc from those exact promotion directories, retain DEBIAN and an explicit
retired/recovery marker. Installed-root before/after full snapshots must match.

Actual gtk-schema-promotion-custody-1 terminal0/complete: eight restores/data/control
checks passed,783540224bytes reclaimed, installed_root_changed_paths0. Available
space18169802752bytes after custody. Source/compiler/test/native package custody
is unchanged. [Exact archives, records, restored entry counts, retired paths and log](../evidence/B02-gtk-schema-promotion-custody.json).

Future cache updates extract the retained current GTK archive into NEW staging,
as already proven by these restore checks; never reinstall GTK merely to recreate
a retired stage. Never replay this retirement. Receipts/markers make interrupted
state inspectable. Current native GTK4toddy8 remains installed with all schema
contracts previously qualified; no GUI criterion is inferred from custody.

Next minimal app branch: frozen GNOME Terminal3.60.0 requires VTE0.84.1 from the
selected frozen BLFS13.1 page. VTE's actual source/options/dependencies must be read;
Fast_float8.2.10/fmt12.2.0/simdutf9.0.0 official source leaves are pinned from that
page before guest use. No compiler networking/moving fallback or silent upgrade.
Qualification/install/PTY/UI/branding/user-configuration checks remain separate.

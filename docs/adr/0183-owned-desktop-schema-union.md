# ADR-0183: Owned complete desktop stock schema union

Status: native stock lookup/key contracts accepted; graphical consumers pending.

NMA/GDM/SettingsDaemon/Shell now own source schema XML, but each DESTDIR build
correctly avoided overwriting the GTK-owned shared generated cache. Prepare one
immutable public input from74actual stock files with exactly one current native
package owner each (16owners), exact hashes and the existing GTKtoddy7 cache.
Do not copy user preferences, silently compile into the installed directory or
rebuild GTK. Reuse the qualified schema_union_build.py in the existing unprivileged
read-only-input/no-route worker.

Strict native compilation and Gio inspection passed. New115schemas/900keys include
33additional schema IDs; all82baseline schemas/623key contracts preserve paths,
types, generic defaults and ranges. Source GNOME desktop-specific Shell overrides
are included unchanged; no existing user values are touched. Count both fixed and
relocatable schemas, unlike Shell's earlier fixed-path-only private count94.
Full descriptions/source owner hashes are retained in the raw evidence.

Controlled native GTK4 same-upstream4.22.4toddy7→toddy8 updates only the shared
cache and legal metadata for its actual source inputs. Verify/extract the exact old
native archive and entire payload, preserve906nonlegal entries except the changed
cache, retain old recovery archive/record. New archive
`2a60562df0937034bfdd514fe09fc25300ac4d62daa8ea797d5b2ecc368cc04d`.
Recipe/post0/0,16changed root paths; new package1973owned entries. Cache SHA256
`824567b089fb951595e4d961162d8f59406a7f70d7b86b9b01de93515bb42a2f`.
Actual installed default-source lookup matches every measured schema/key contract;
package audits0, no schema/module override or library/configuration rebuild.
[Build, complete transaction, installed lookup and raw evidence](../evidence/B02-desktop-shared-schema-union.json).

Runtime lookup availability is not working GDM/login/desktop/network/audio/input
or a tested hardware provider. Deprecated/optional xsettings and device schema IDs
remain upstream data, not an advertised built plugin or hardware capability.
Next: first actual native Shell session and required graphical interaction, then
remaining minimal applications/service/offline/resource gates. B02 remains open;
complete all B02 and then stop as requested by the owner.

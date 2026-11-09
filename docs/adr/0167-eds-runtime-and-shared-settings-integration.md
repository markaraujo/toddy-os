# ADR-0167 — EDS calendar services and shared settings integration

Date: 2026-11-09. Status: selected profile; verified outcomes linked below.

Use frozen Evolution Data Server3.60.2 with already owned libsoup3.6.6,
libical4.0.5, NSS3.126/NSPR4.40, libsecret/GLib/GTK3/GTK4. The actual source
explicitly supports libical4; no foundation/ABI upgrade is needed. Enable both
GTK bindings, introspection, SMIME and original tests. Omit optional WebKit OAuth,
GOA, weather, Kerberos/LDAP, phone library, Vala/docs/examples and legacy BDB
migration through supported switches; retain SQLite calendar/contact storage.
No online-account, mail-client or real-provider acceptance is inferred.

Initial configure selected Canberra-GTK3, which the qualified Wayland core sound
profile intentionally omits. Reconfigure only that supported optional EDS alarm
extension off; preserve actual core sound packages and mandatory B02 desktop audio
validation. Legacy EDS alarm sounds are not advertised. The initial configure
failure is retained, without source extraction or successful dependency rebuild.

All101 enabled original CTest programs passed, including actual private D-Bus
source/calendar factories, create/modify/remove, offline caches and SQLite. Original
logs/JUnit and799 compiled ELF objects are retained. Own additional C consumer
first mistook exported version variables for functions, then lacked staging-only
private libedbus discovery. Correct only those consumer inputs/search paths;
consumer4 passed with all original artifacts/589 staged regular files unchanged.
No original suite/stage replay or production library patch. Native package
install/post0/0 changed659paths/853owned entries. Actual installed C/SDK/GI,
private-library resolution, UTF8/ICS/source identity/malformed refusal/prior-state/
two-cycle recovery pass. Installed service activation remains a separate check.

## Shared schema owner

EDS installs six XML files; earlier GNOME Session and keyring schemas were also
not in the GTK-owned cache. Never overwrite that cache ad hoc or package another
owner's files with EDS. Prepare exact55 public owned schema inputs from10 current
package owners (including the GLib-owned gschema.dtd), read-only and without user
preferences. Strict private compilation and actual Gio lookup preserve all67
existing schemas/500keys with identical paths/types/defaults/ranges. Add nine
schemas/71keys, total76/571. No old default changed.

The native transaction must keep GTK4.22.4 binaries intact, replacing only owned
cache/legal metadata in revision toddy5, preserving dependencies and retained
old archive/record. Exact GTK revision reverse pins were checked absent. Verify
all old nonlegal payload entries except the declared cache and check actual
installed default-source schema/key contracts, dpkg/APT and SDK. Rollback is
specified from retained inputs; it is not an executed recovery claim.

After native cache verification, check only affected installed EDS service/
persistence operations with private user data/bus, then continue GNOME runtime
prerequisites. Actual GNOME login/GUI/offline/network/audio and physical hardware
remain pending. Fresh combined build/qualification portability remains explicit
Phase2 work; retained historical partial jobs are not a fresh-build success.

[Owned EDS](../evidence/B02-evolution-data-server-install.json).

## Verified shared cache and installed service outcomes

GTK revision toddy5 install/post0/0 changed24paths. All906old nonlegal entries
except the declared cache remained unchanged; default installed76schema/571key
contracts passed with no overrides. [Cache proof](../evidence/B02-shared-schema-union.json).

Actual installed EDS services then passed as UID101 in private mount/network
namespaces (only four standard character devices, loopback and zero external
routes), private HOME/XDG and two distinct real session buses. No EDS_TESTING,
module/library/schema override, real accounts or user preferences. An event was
created/read, actual ICS file observed, buses/services exited, the next bus read
the persisted event, pre-cancelled read was refused, normal read recovered, and
removal/disk state verified. Services required no forced termination; private
profile removed. Full-root transaction recipe/post0/0 with ZERO installed changes.
This proves installed service/storage behavior, not GNOME GUI or physical audio.
[Native service proof](../evidence/B02-eds-installed-services.json).

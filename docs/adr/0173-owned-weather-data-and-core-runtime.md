# ADR-0173: Owned weather data and scoped offline GWeather runtime

Status: data and core library accepted; stock-schema integration has separate evidence.

## Actual data generation and source scope

Use the frozen gweather-locations2026.2 source selected by ADR0172. Its original
XML validity driver passed. Python/GI generated the native-endian GVariant and
the actual typed-data probe checked normal form,8862locations/245country entries/
332timezones, every index/parent link, BR/PT, SBGR/LPPT coordinates and Sao Paulo
zone lookup against the unchanged source. Optional pylint was not available or
registered; it is not a pass. This is static source data, not actual owner position
or forecast/provider coverage. Native architecture is amd64, never architecture-all.

The first native read-only qualifier expected an original test name without its
actual Meson lint-suite prefix. It stopped before staging/archive/install, root
changes0; absence of all three was checked before a new step. Correct only that
metadata expectation, never repeat generation/original XML/stage. Native install2/
post0/0 changed110paths and owns299entries; installed GVariant/SDK/APT invariants
matched the accepted stage. Exact GPL source notices are retained.
[Data evidence](../evidence/B02-gweather-locations-install.json).

## Library source, actual failed external original and core qualification

Build pinned libgweather4.6.0 with already owned Soup3, Geocode API2.0, JSON-GLib,
libxml2, GLib and the data package. GI4.0 remains enabled; optional Vala/API docs
are omitted through source options, and the optional weather API key is empty.
Three original core drivers passed12cases: location/serialization/lifetime,
duplicates and timezones. The fourth original metar program is a live HTTPS
comparison with the complete aviationweather.gov station registry. It failed
SIGABRT on DNS in the deliberately no-route compiler namespace. This actual failure
is preserved and unqualified; no fixture/timeout/absence-of-log substitutes a pass.
Remote provider/station validation is outside this offline basic-library scope.
Native reference-network/browser validation remains required before B02 acceptance.

Do not expose external networking or credentials to a compiler to fix that test.
Resume staging and the own offline consumer only, retaining all42original ELFs
and raw test records; no compiler/core-test replay. The actual C consumer checks
BR/PT and station coordinates from the owned database, location variant roundtrip,
wrong-type refusal and two recovery cycles. Stage regular files125. Native
install/post0/0 changed200paths/398owned entries; installed library/C/GI4.0/SDK/APT
passed with no build module/library/data override. Info/default schema integration
is a separate next boundary, not inferred from location-only API tests.
[Library evidence](../evidence/B02-libgweather-install.json).

## Notices and bounded external-input review

Retain source GPL2 COPYING and per-file leading notices, including LGPL and
kdtree's three-clause BSD terms. Package the existing complete LGPL2.1 common text
with pinned repository path/hash in the component inventory, without modifying
upstream notices or importing another component's executable code. Per-file
conditions remain in force. Original remote JSON/XML/provider formats remain
external data, never a privilege/publishing permission source. The source data
used here is pinned, sized and typed; this does not qualify arbitrary network XML,
remote station registry freshness, location permission UI or actual forecasts.
No service/owner location tracking is enabled by installing these libraries/data.

## Shared schema owner integration

Prepare a NEW union from actual current owned schema inputs, preserving all prior
81schemas/618keys and adding exactly org.gnome.GWeather4/five keys for82/623.
The existing qualified strict schema compiler/contract comparator is reused;
installed preferences are never changed. GTK4 remains the shared cache owner,
same-upstream4.22.4 native toddy6→toddy7, cache/legal-only, unchanged dependencies.
Old archive/record and explicit transaction receipt retain recovery evidence;
no old schema transaction is replayed. Installed default-source lookup and a
GWeather Info create/update/abort/recovery probe with providers disabled, memory
settings, UID101 and private no-route network namespace are separate postchecks.
No full GNOME/GDM, keyboard/focus, physical hardware, forecast or owner-position
acceptance follows from this integration.

### Actual shared-schema and Info result

Native same-upstream GTK4toddy7 install/post0/0 changed6paths and preserves906old
nonlegal entries;1965owned entries. Actual default schema source82/623 matches the
strict private union, preserving all81/618 previous contracts. Native Info probe
passed two create/update/abort/recovery cycles as UID101 with no schema/module
path override, private network namespace, providers disabled and memory settings.
This does not qualify cancellation of a real in-flight provider request. User
preferences and dependency controls remain unchanged. No GTK runtime rebuild,
old schema transaction or unchanged original suite was repeated. Source/raw
receipts are retained; no active writer remains.
[Stock schema/Info evidence](../evidence/B02-gweather-shared-schema-union.json).

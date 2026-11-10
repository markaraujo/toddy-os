# ADR-0172: Pinned geocode and weather-data prerequisites for GNOME Shell

Status: Geocode runtime accepted; weather data build pending.

The selected GNOME Shell50.4 source requires GWeather. Its already frozen
libgweather4.6.0 source requires geocode-glib and gweather-locations. Follow only
these actual dependencies; do not restart desktop selection or substitute a
full GNOME app collection. No weather API key, location permission or account is
required to build or use the offline desktop. Installing the geocode library
creates no location-tracking service or owner permission grant.

## Frozen sources and compatible API

Use the exact required frozen BLFS13.1-systemd parent edges:

- geocode-glib3.26.4, gnome/geocode-glib.html pageSHA
  a2cb829d61ee0b6dc476e66a4cf29169484abc93c728f310476a3ccbb3c6b448;
  sourceSHA2d9a6826d158470449a173871221596da0f83ebdcff98b90c7049089056a37aa.
- gweather-locations2026.2, gnome/gweather-locations.html pageSHA
  847131169d5d825c4358452a6a2c8e4b3206e117a4d000b0d0b9d9204e87c75f;
  sourceSHAe7570a3661e0a752a06387b2032585cf588fc56770b1f9f39f1a55d17b2835fe.

Both official versioned HTTPS archives match their frozen legacy book MD5;
SHA256 was frozen before guest extraction. No independent publisher signature
is claimed. No accepted foundation component is upgraded or rebuilt.

Actual geocode source supports Soup2/API1.0 or Soup3/API2.0. Select Soup3/API2.0
with the already owned libsoup3.6.6, GLib/JSON-GLib and introspection. Keep original
test compilation while omitting installed-test payload and optional API docs.
Library terms are LGPL-2.0-or-later; installed Maki icons use the retained
three-clause BSD notice. Original OSM JSON mocks are source fixtures, not live
geocoding or installed test/data payload. Per-file source conditions remain in
force and exact source legal notices are retained.

## Actual Geocode qualification

The isolated no-route UID101 build/stage completed0. Two original Meson drivers
(Geo URI and Test mock backend) passed, plus unchanged original API paths distance,
zero-distance and osm_type. Foreign-locale JSON/API cases are explicitly not
qualified; do not fabricate their acceptance or generate global locales for them.
Own C consumer verifies UTF8 description, geo-URI roundtrip, malformed URI refusal
and two recovery cycles.23compiled ELF objects/27staged regular files retained.

Native3.26.4-1+toddy1 install/post0/0 changed43paths/50owned entries. Actual installed
library loading with no stage override, C refusal/recovery, API2.0 pkg-config,
GeocodeGlib2.0 GI UTF8/coordinates and APT consistency passed. This is library/ABI
acceptance, not remote geocoding, actual owner position, permission UI, forecasts,
complete GWeather or GNOME graphical acceptance. Never repeat accepted build/
originals/stage/install to move to the next dependency.
[Evidence](../evidence/B02-geocode-glib-install.json).

## Next data boundary

Weather source build instructions have been inspected, but no guest data input/
work/job or recipe exists yet. The actual Python/GI generator converts the pinned
Locations.xml into typed GVariant Locations.bin. Upstream explicitly declares
host-endian dependence, so do not label this generated binary architecture-all.
Keep XML/DTD/pkg-config/translations and exact GPL-2.0-or-later source notices.
Qualify source-to-data invariants, normal-form/schema/index bounds, representative
Brazil/Portugal/timezone lookups and source hashes. Optional xmllint/pylint checks
must remain distinct from runtime data validation. Then build libgweather and
integrate any new stock schema through its actual owner, preserving81schemas/
618key contracts. No location/provider permission is inferred from static data.

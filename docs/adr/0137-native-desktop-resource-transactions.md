# ADR-0137: Independent native resource packages and owned schema integration

- Date: 2026-11-08
- Status: Accepted; native resource build/probe and owned transaction verified
- Sources: frozen Hicolor0.18, Adwaita icons50.0 and GSettings desktop schemas50.1

Build these three prerequisites in one serialized unprivileged job with independent
stages, native archives and provenance. They register no executable upstream test
suites; record zero, never empty-suite passes. The actual Adwaita Meson source
chooses gtk4-update-icon-cache before its GTK3 fallback. The already owned GTK4
tool satisfies this dependency; no additional GTK3 build is needed for this slice.

Upstream suppresses global cache generation under DESTDIR. Generate and validate
icon caches privately against the complete installed stock icon union plus each
new theme. Put only the cache into its theme owner's stage; do not copy foreign
GTK icon payload into that package. Generate a strict private schema union from
the actual GTK/GLib and new GNOME schema files. Verify native schema lookup, actual
default Adwaita Sans/Mono fonts, GDesktop enum metadata, named icons, real SVG-to-PNG
decode and Xcursor data. This is not window/focus/pointer interaction acceptance.

The initial probe incorrectly requested value_nick from an unregistered plain C
enum. Its frozen header declares ZOOM=5. Correct only this assertion and run a
probe-only recovery with all stage file/link hashes unchanged. Original consumer
failure remains evidence; no build/cache generation or successful suite replay.
Actual recovery0:52 schemas, expected fonts, two icons,32x32 SVG/PNG and cursor magic.

Own the three resources independently. Compare the actual installed schema input
file set/hashes with the qualified private union before promoting its cache.
GTK already owns gschemas.compiled: rebuild its native archive as4.22.4-1+toddy2
from its verified original payload, changing only that generated cache and required
source/legal metadata. Verify every other runtime payload entry is unchanged.
Keep both archives/records and a per-package transaction receipt; never replay an
interrupted install. User dconf/preferences and home directories are not inputs or
mutation targets. Future schema/icon/MIME changes need their own controlled owner
transaction and affected checks, not arbitrary imported maintainer scripts.

The small resource job uses a separate bounded512MiB regular-file volume in the
disposable builder, with the same UUID/path/one-writer/NoNewPrivs guards as ADR0135.
Host100GiB plus full512MiB capacity and256MiB margin is checked before creation.
The GTK volume/tests remain intact. No target partition or physical disk changes.

Actual native three resource packages and GTK4.22.4-1+toddy2 schema/legal-only
upgrade installed/post0/0 in70.624s. Other GTK runtime payload entries unchanged.
Installed cache validation/native52schemas/fonts/GI/icons/SVG/cursor APIs0. Original
enum-property probe failure retained;938 staged files/links unchanged in recovery.
The native window/session/media gates remain pending.

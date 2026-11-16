# Native GNOME branding inputs

These are repository-prepared source inputs for the planned `toddy-branding`
package. Nothing in this directory installs itself, changes the development host,
starts GNOME, enables an extension or completes B11 acceptance.

- `package-map.json` maps existing artwork to owned package destinations. It
  references the current asset manifest instead of duplicating source PNGs.
- `toddy-backgrounds.xml` lists the four approved navy/plain/branded wallpapers.
- `90-toddy-branding.gschema.override.in` is an inactive distribution-default
  template. B11 renders its final suffix and validates against the exact guest
  schemas before compiling through native package hooks.

## Package responsibility

`toddy-branding` owns shared wallpapers, the background catalog and Toddy identity
exports. The future assistant package depends on it rather than claiming the same
files. The `.desktop` input lives in ui/phase2 and belongs to the assistant, so
installing artwork cannot expose a launcher for an absent executable.

Apply defaults without dconf locks, a startup daemon or a login-time `gsettings
set` loop. Explicit user settings win after install/update. Test that preference
survives logout, package upgrade and dark/light changes. Removal must leave a
usable upstream fallback and report a removed wallpaper dependency without
silently resetting unrelated user preferences. Package hooks/ownership and actual
removal behavior are future B11/B12 work, not a claim made by these source inputs.

The theme stays Adwaita-based. Use supported dark/light/accent APIs/settings,
app-scoped Toddy styling and semantic suggested/destructive controls. High-contrast
and user font/scaling settings take precedence over decoration. Do not inject a
web stylesheet into GTK, patch GDM resources or replace unrelated app CSS.

A Shell extension is not the branding package. Only a proved shortcut/presentation
gap justifies a small version-pinned extension later. It contains no model calls,
credentials, policies or privileged logic. The ordinary app launcher remains the
fallback, and disabling the extension must leave both GNOME and Toddy usable.

## Reusable artwork and limits

Keep the current 1672x941 wallpaper bytes; do not claim 4K by upscaling. Native
size/crop/multi-monitor behavior still needs guest review. The exact original
transparent mascot is the icon master. Planned PNG icon exports require a small-
size readability review; no traced/generated SVG is a real vector master.

Using the owner-approved mascot as the assistant identity is an intentional brand
choice rather than a claim of full conformity with every generic GNOME icon-style
recommendation. Website expressions and simulated UI screenshots are explicitly
excluded from the runtime payload. Never put supporter/Patreon copy or web-only
animations into the native agent by copying the website bundle.

Sources reviewed 2026-11-07:

- [GNOME custom defaults](https://help.gnome.org/system-admin-guide/dconf-custom-defaults.html)
- [Background catalog format](https://help.gnome.org/system-admin-guide/backgrounds-extra.html)
- [GSettings](https://docs.gtk.org/gio/class.Settings.html) (API 2.0; current docs are not the frozen guest version)
- [GNOME styling](https://developer.gnome.org/hig/guidelines/ui-styling.html)
- [Extension anatomy](https://gjs.guide/extensions/overview/anatomy.html)

## Native package staging source

`scripts/build/phase2/branding_stage.py` now stages the exact approved sources as
owned inputs for `toddy-branding`. Run `python3 scripts/build/phase2/branding_stage.py
desktop <repository> <new-stage>`; it refuses existing output and verifies pinned
artwork hashes/dimensions. No original PNG is edited or resized. The current map
has pending icon sizes, with no approved exports to reuse, so the exact mascot is
staged at `/usr/share/pixmaps/io.github.markaraujo.Toddy.png`. The generator prefers
an explicit verified `icon_exports` map when those approved files exist. Native
32/48/64px readability remains required; a fallback does not earn that acceptance.

The default stage contains no active schema override, preference lock, launcher,
login process or GDM patch. Optional override staging requires an exact guest
schema-validation callback and returns a required controlled schema-cache rebuild;
it does not run that cache mutation on the development host. Native ownership,
generated-resource custody and install/update/removal remain the existing package
transaction's responsibility, including user preference preservation.

B02's `toddy-desktop-defaults` dconf database outranks GSettings schema defaults.
Its existing owning recipe can use `render_desktop_defaults(canonical_keyfile)`
to replace only the three provisional empty-background defaults with approved
wallpaper URIs and zoom. The renderer refuses an edited/unknown background
baseline, keeps every other section and does not own a second conffile or alter
an installed/user file. Rebuild that package's existing native dconf database
through its controlled transaction; do not force a setting at login. Actual
guest defaults, upgrade/removal, preference preservation and screenshots remain
unverified by this source preparation.

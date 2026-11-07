# Navy brand and static UI preview verification

Date: 2026-11-07. Scope: repository assets and browser design concepts only.

## Protected identity and provenance

- Logo SHA-256 unchanged: eb46f81175fca698345870eee2101664ec613ff2de4c2430ef9b4fa27f3a1a81.
- Mascot SHA-256 unchanged: c743d555c274b317f5832ee47609332d80f40a2d370b278b25706f60eedcf45c.
- Three backgrounds generated with the built-in image tool, actual 1672x941 PNG.
  Prompts and limitations: assets/brand/generation-record.json. No 4K/vector claim.
- Four 1320x680 browser-rendered concepts from ui/preview.html at 1440x1000:
  desktop, quick entry, task and installer. Original mascot layered by HTML;
  all exports carry their own simulated-design label.
- Previous background PNGs and metadata preserved under assets/brand/archive/v2.

## Focused visual/browser checks

Playwright, local exported page/preview server, desktop 1440x1000 and mobile
390x844. All four preview scenes activate, no horizontal overflow. Dark/light
control sets the intended palette. Installer Previous/Next reaches 4/4, disables
Next at the end and returns to 3/4. Visual inspection of desktop/installer/light
background and desktop/mobile page captures completed; no runtime OS claim.

Static semantic contrast pairs, calculated from the sRGB relative luminance
formula (ratio): ink/midnight 17.01, muted/navy 8.02, accent/navy 8.06,
light-ink/light-background 13.38, light-muted/light-background 6.11 and
light-accent/light-background 5.90. All these selected text pairs exceed 4.5:1.
This is not a complete accessibility audit of every pixel or third-party app.

No GNOME, model, driver or installer was built or tested. Guest B11 is not
accepted by these assets. Published foundation ISO is unchanged.

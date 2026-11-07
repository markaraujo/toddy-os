# Installer visual preparation — 2026-11-07

Scope: existing browser study and reusable native visual handoff only. B stories
remain unstarted; this is not installer/boot or S17 runtime acceptance.

- Reused exact approved mascot, navy boot background and four existing labeled
  GNOME concepts; no raster redesign, duplicate frame sequence or new preview page.
- Added collapsible boot/completion bookends and a 240 ms scene transition.
  Reduced motion disables decorative animations; boot dots run only when open.
- Added source motion inputs and stage/component ownership under
  assets/brand/installer; B11/B12 now explicitly join the pieces using real
  installer events, supported native adapters and verified completion.
- make check: 197 tests passed in 0.202 seconds. make site exported the allowlist.
  node --check accepted translations.js; git diff --check passed.
- Playwright: desktop 1440x1000 and mobile 390x844, no horizontal overflow;
  loaded images valid, Next changed 1/4 to 2/4, no page JavaScript errors;
  reduced-motion computed animation name was none. Visually inspected the desktop
  capture. Exported page loaded correct headings/images in all six portal locales.

Browser captures are temporary local QA outputs, not new shipped screenshots.
Real target toolkit, boot presentation, input/accessibility, cancellation, disk
operations, progress/error and completion behavior remain B02/B11/B12/B13 proof.

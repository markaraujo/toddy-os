# Portal responsive layout correction — 2026-11-07

The owner reported a broken public layout after the mascot update. Playwright
reproduced a clipped Portuguese hero at 390 CSS pixels on GitHub Pages:
`.hero-copy` measured 417.906 pixels wide, ending at x=439.906 inside a
390-pixel viewport. The hero's overflow clipping concealed this from a check
of document scroll width alone. Spanish also exceeded the viewport at 320.

Use zero-minimum grid tracks and children, a fluid mobile heading size and
emergency wrapping for translations. Exported HTML now includes content hashes
in CSS/JavaScript URLs so refreshed HTML cannot reuse an incompatible cached
resource under the same unversioned URL. Cache staleness was a preventive fix,
not the confirmed cause of the reproduced clipping.

Focused Playwright checks against the exported local site passed for all six
languages at 320, 390, 768, 1024 and 1440 pixels: no main/header element extended
past the viewport and no horizontal document overflow. Inspected Portuguese
mobile and full desktop screenshots after image decoding. All referenced images
decoded; the hover yawn entered playing and returned to idle. Screenshots remain
local under /tmp/toddy-pt-before.png, /tmp/toddy-pt-after.png and
/tmp/toddy-fixed-desktop.png, not permanent release artifacts.

`make check` passed all 184 existing checks; the public-export test additionally
checks the deployed stylesheet digest. No OS build or runtime acceptance changes.

# Full portal copy review and supporter wall — 2026-11-07

## Delivered scope

Reviewed the complete landing template, its four dynamic preview descriptions,
generated progress labels, author/support copy, supporter acknowledgment and
footer. Rewrote the opening explanation, preview headings/descriptions, three
feature explanations, installer introduction, wallpapers, roadmap introduction,
release guidance and footer in direct language. Retained the approved brand
headline, deliberate interactive mascot jokes, factual metadata, accessibility
labels, technical story criteria and legal attribution where appropriate.
Technical story sources and current phase state remain unchanged. Planned desktop
features are described as future work, separate from the downloadable foundation.
All changed public copy has entries for the existing six portal languages.

Created a dedicated supporters.html with a navy night sky, the unchanged original
mascot, subtle CSS twinkling/orbits/shooting star, hover tilt and equal-sized name
cards. Reduced-motion preference disables ambient/hover movement. No particle
library, canvas loop, analytics or Patreon API is added. Decorative stars are not
supporter records. The empty wall contains no invented public names.

## One-file updates

config/community.json remains the only data file an owner needs to edit to add
or remove approved names. The export renders the wall from current JSON each
time, without requiring generated name lists to be committed. make dashboard
also creates an ignored offline wall. Canonical template/styles stay separate.
See config/README.md. This is automatic build-time publication, not a live sync
of payments. Display names are validated, HTML-escaped, untranslated and published
only with permission; no donor contact/payment data is stored publicly.

## Basic verification

- Playwright checked both pages in en/pt-BR/es/zh-Hans/ja/ru at
  320/390/768/1440 CSS pixels: 48 combinations without viewport overflow.
- Selected all four preview tabs in every locale and checked localized titles.
- Inspected the complete Portuguese landing and supporter desktop/mobile captures
  under /tmp/toddy-complete-review.png and /tmp/toddy-supporters-*.png.
- Followed the landing supporter link and confirmed language carried over.
- Confirmed normal CSS animation names and reduced-motion stars/orbits/shooting
  star all returning animation-name:none.
- A focused fixture checks empty/populated one-file rendering and HTML escaping.
- make check: 185 tests passed; translations.js syntax check passed.

No OS build, hardware validation, Patreon payment verification or release-scope
acceptance is claimed. No approved brand image bytes were changed.

# Public portal localization, independent authorship and real-icon checks

Date: 2026-11-07. Scope: static public portal and design concepts, no OS build.

## Delivered behavior

Six supported locales: en, pt-BR, es, zh-Hans, ja, ru. First visit uses browser
language, a stored manual preference overrides later automatic detection, and
?lang= explicitly chooses a shareable locale. Unsupported languages fall back to
English. Native-name selector stays available on main/preview/slideshow pages.

No external translation API, font/CDN dependency or new application framework.
Translation uses local strings/text/attribute updates and never executes supplied
HTML. Translated title/description, document lang, captions, accessibility labels,
roadmap titles/status/counts, author/release copy and slideshow text stay coherent.
Technical acceptance/source documentation is explicitly English; conceptual OS
screens/PNG artwork retain their original English labels.

Added visible independent author Marcos Araujo, experimental-preview notice,
release/history links and the future 1.0 target without inventing a stable release
or date. Actual downloadable foundation still excludes desktop/assistant.

Replaced approximate dock/folder/control shapes with actual unmodified GNOME and
Adwaita SVGs. Exact sources/package versions/commits/hashes and retained notices
are in assets/third-party/gnome. Four 1320x680 concept PNGs were recaptured at
1440x1000 with ?lang=en; original Toddy logo/mascot hashes are unchanged.

## Focused checks and observations

- make dashboard / make site / make check: passed; 184 existing local checks,
  0.179 seconds in the six-locale run. No full OS/upstream test suite run.
- Existing export boundary check caught unrevised ../ui script paths; corrected
  source rewriting and reran successfully. Export remains an explicit allowlist.
- Fresh Playwright contexts with pt-BR, en-US, es-ES, zh-CN, ja-JP and ru-RU browser
  locales selected the intended translation; fr-FR selected English.
- Stored Russian preference overrode a Portuguese browser; explicit Spanish query
  overrode that saved setting. Switching through all six locales and back to
  English preserved preview/filter behavior, translated captions and 13-story counts.
- With localStorage get/set deliberately unavailable, selection still worked.
  An initial dynamic-link check exposed a missing href mutation hook; corrected
  it. Portuguese selection then persisted through assistant preview navigation
  via ?lang=pt-BR#quick without storage access.
- 1440x1000 desktop and 390x844 mobile: no horizontal overflow across all six main
  page languages. Japanese/Russian slideshow next actions update localized copy.
- Actual icon rendering inspected visually; six folder SVGs, four app dock icons
  and nine status-bar symbolic references across three desktop scenes were present.
- Protected identity hashes verified against brand manifest; updated screenshot
  hashes and third-party qualifications recorded in the brand provenance files.

Browser checks are basic representative validation, not native-speaker review,
full accessibility certification or evidence of a working graphical OS release.
PayPal integration requires the public donation link supplied by the owner; no
account identifiers, credentials or fabricated donation target enter this evidence.

The owner simplified donation recognition to a single optional public supporter
name, without paid tiers. config/community.json starts with no URL and no names;
no guessed donation target or fake supporters are shown. A translated acknowledgment
section is prepared; add only owner-supplied public PayPal URL and approved names.

Final exported-page pass covered all three public surfaces across all six
languages at 390x844: no horizontal overflow or JavaScript page errors. All main
page images decoded after eager loading for inspection. All 77 local exported
HTML references resolved inside the explicit public tree. Supporter text translated
correctly, and zero PayPal links were rendered while donation_url remains null.

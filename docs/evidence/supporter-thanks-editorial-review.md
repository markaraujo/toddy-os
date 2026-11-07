# Editorial refinement of supporter thanks — 2026-11-07

## Review performed

Read all 100 EN/PT pairs, rewrote the full catalog and adapted every entry to the
other four portal languages. Made two additional passes for meaning, repeated
jokes, awkward wording and standalone use after a randomly selected predecessor.
The 100 entries remain distinct in each locale.

The greeting already names and thanks the selected person. Each continuation now
acknowledges support, kindness, encouragement or company, with a concrete dog
observation where it helps. Humor rests on Toddy's own habits: closeness, laps,
walks, cushions, short legs, glasses, snacks, supervision and the visible galaxy.
A few direct sincere lines avoid turning every thank-you into a forced punchline.

Removed or replaced obscure images (the human behind the dog's glasses),
transactional approval/rewards, gross/ambiguous doorstep gifts, repeated sniff
certifications, dismissive attention jokes and assumptions that every supporter
joined at the beginning. Do not interpret mascot narration as payment verification
or a promise of product delivery. The editorial rules are now in ui/README.md.

## Validation

- Existing catalog test verifies 100 distinct entries in all six locale columns;
  make check passed all 186 tests in 0.192 seconds.
- Playwright selected each revised phrase with a controlled random source in each
  locale: all 600 displayed translations matched, with the approved name intact.
- Mobile verification found no horizontal overflow; the starfield retained one
  vertical position across all 100 responses per locale.
- Inspected Portuguese mobile and desktop screenshots under
  /tmp/toddy-thanks-refined-mobile.png and /tmp/toddy-thanks-refined-desktop.png.
- JavaScript syntax validation passed. Selection/randomization, page layout,
  motion behavior, names and brand image assets were not changed.

This is an authored copy review and browser verification, not a native-speaker
certification of all languages or a new OS acceptance claim.

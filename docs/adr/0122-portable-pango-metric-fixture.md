# ADR-0122: Independent portable Pango font-metric fixture

- Date: 2026-11-08
- Status: Accepted qualification method; native execution and installation pending

## Evidence and boundary

Frozen Pango1.58.2 compiled. The original driver hardcodes approximate character/
digit widths49273/58368 for Boxes. Source tests/fonts/boxes.ttx only maps A-P/Z
and a missing-glyph space; it does not supply lowercase/digits. Original
pango/pangofc-font.c derives these two metrics by laying out the language sample
and0123456789, using font fallback where the face lacks coverage.

Actual unchanged binaries produced different derived metrics with three controlled
font sets. Curated Cantarell corrected two other layout failures, while this
reference remained failing. Boxes own ascent/descent/decoration and exact glyph
geometry cases passed. Preserve all failed jobs and the two-correction budget in
B02-pango-pending.json and the private failure ledger. Do not relabel the original
fallback-dependent golden passed or run a third font-selection guess.

## New independent input

Create a separate test-only full-ASCII cmap from the authenticated original
Boxes.ttf/boxes.ttx. Preserve all existing nonzero character mappings, glyph
outlines, hmtx and other referenced tables. Missing printable ASCII maps to the
existing A glyph. Both TTX and font headers must independently specify1024 units
per em; every used glyph has1024 horizontal advance, and advance-changing
kern/GSUB/GPOS tables must be absent. Thus at absolute100px every sample character
has an exact100px advance, independent of external fonts. Repair only cmap and
standard head/full-font checksums. Retain the original font and notices unchanged.

The deterministic derived font SHA256 is
4a9a161f3afb5e7897bff0f4f1341686d8536b8630e9edd22d60118ccc2c92d2.
A host-only independent FreeType/fontconfig scan recognizes Boxes and exactly
printable ASCII20-7e. This is input preparation, not native product acceptance.

A separately compiled portable variant of the same original driver changes only
its private test-font path and the two derived reference widths to100*PANGO_SCALE,
which follows the font geometry rather than any observed Pango result. Keep all
other own-face/glyph assertions. Verify the actual English sample is covered,
execute all three cases natively, bind original/adapted source and font hashes,
and prove every original library/test binary unchanged. This does not patch or
rebuild the Pango library or the original test binary.

## Acceptance still required

Do not install/accept based on this ADR or the host scan. A new native oracle job
must succeed after the exclusive guest writer is free. Keep the original failure
visible and label the portable variant separately. Reuse the nine unchanged core
passes and nineteen curated font-driver results (including two programs with no
TAP cases), with exact input identities; do not claim a wholly passing unmodified
upstream suite. Installed native Portuguese wrapping/markup/pixel rendering, Python
binding and ownership/ABI checks remain mandatory, as do actual GTK/GNOME UI checks.

This is a concrete new geometry reference, not a reset of the exhausted old
font-permutation budget. If the independent oracle fails, preserve that new input/
result and apply the same bounded diagnosis rules. No package stage or B02/G2
criterion is preaccepted.

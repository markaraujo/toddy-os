# ADR-0134: Preserve the SVG golden failure and qualify selected Pango geometry

- Date: 2026-11-08
- Status: Accepted for the experimental native renderer profile; original golden remains failed
- Sources: frozen librsvg2.62.3 and Pango1.58.2 archives in sources.lock.json

Native librsvg compilation passed. Four of five registered upstream drivers passed.
The rsvg driver executed its complete set and found one reference failure:
text-text-03-b,753 other reference cases passed. Reproducing only the existing
compiled case with its original manifest environment preserved the failure and
144 ELF hashes. Original suite/case failures remain evidence, never counted as
passes. No reference image, fixture, source byte or global tolerance changes.

The image differs in exactly12 pixels at the two ends of the fuchsia strikethrough
on the text “Line through”. There are no changed pixels elsewhere. Pango1.58.1
NEWS explicitly records synchronized over/under/through lines; the selected1.58.2
inherits that implementation. Its pango-renderer.c add_strikethrough uses the
minimum ink/logical x and maximum ink/logical width. The old reference covers only
ink bounds. Librsvg text.rs explicitly requests a Pango strikethrough attribute.

Compile an independent native Pango/Fontconfig/Cairo consumer from the unchanged
bundled test fonts and exact fixture text/size/origin. Measured logical width is
177.484375, ink x2.640625/width172.71875, origin39, baseline147. Selected Pango
therefore extends the strike to x39..216.484375 instead of the golden's
x41.640625..214.359375. Strike y139/height1.59375 accounts for both affected rows.
The oracle examines every actual/reference pixel and rejects changes outside
those independently derived endpoint regions or outside the fuchsia decoration.
Actual oracle exit0,12 changed pixels and no other changes.

Accept this narrowly identified compatibility exception for the selected
experimental native renderer. Retain the original failed golden and source-backed
geometry result together. Still require native SVG/Cairo exact color pixels,
malformed input refusal, real staged and installed Gdk SVG loader, owned generated
cache update and GI/PNG regression checks. This does not accept a desktop window,
physical GPU or a general pixel-tolerance exception. Other failures block promotion.

Only finish staging and new consumers after this check. Do not rebuild the144
existing compiled ELFs or replay four unchanged successful drivers. Future input
changes must requalify the affected evidence. Native graphical interaction and
release gates remain pending.

Reproduction on a fresh designated target: prepare the locked librsvg input and
run its original build/test job. If and only if its exact recorded single golden
failure occurs, run librsvg_reference_diagnose.py (default persistent directory3),
librsvg_strike_qualify.py and librsvg_finish.py in the same compiler sandbox/work
directory as jobs reference-diagnose-3/strike-oracle-5/finish-6. Their original
failure/geometry/unchanged-binary guards remain required. The historical missing
manifest diagnostic2 and exploratory oracle4 are retained evidence, not required
reproduction steps. The owned installer verifies these exact qualifier bodies,
then replaces only the original image package's generated cache as GdkPixbuf
2.44.7-1+toddy2. No library recompilation, foreign ownership change or arbitrary
maintainer script. Later loader acquisition/removal requires a new controlled
registry/cache transaction and affected image checks.

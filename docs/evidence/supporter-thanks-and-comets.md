# Random thanks and comet tails — 2026-11-07

Removed the selected-name SVG connector entirely at the owner's request. Bones
now have tapered, layered comet tails and a luminous head, using inline vector
geometry shared by both background meteors.

Each name activation displays one of 100 authored humorous thank-you lines,
randomly selected locally and excluding an immediate repeat. The catalog contains
100 complete lines in all six existing languages (600 text entries), with no AI
request, API, tracking or donor-data sync. The approved name is inserted as text
and remains untranslated. ui/supporter-thanks.js is the editable phrase source.

A continuous 1.3-second grateful nod and subtle halo accompany the response.
The portrait remains the same image. Rapid clicks begin from the current pose,
cancel the preceding response animation and keep at most one active nod/halo.
Breathing is on a separate wrapper so it does not jump when a nod starts/stops.
The caption has fixed available height to avoid moving names as text changes;
long text can scroll. Reduced motion cancels these effects while preserving text.

## Focused checks

- Playwright stepped through all 100 lines in every language with a controlled
  random source: all 600 localized responses matched their catalog entries.
- 100 ordinary random activations produced 67 distinct lines and no adjacent
  repeats; the starfield retained one vertical position through all updates.
- Both pages in six locales at 320/390/768/1440 widths: no horizontal overflow.
- Native touch selected the 50th demo name and produced its localized response.
- After the reduced-motion change event settled, no nod/halo animation remained;
  stars/breathing/meteors were disabled. Keyboard response text still worked.
- Inspected /tmp/toddy-comet-tail.png with the meteor sampled in flight; the
  connector is absent and the bone has a clearly visible tapered light tail.
- make check: 186 checks passed, including catalog completeness/uniqueness and
  the strict public export allowlist. JavaScript syntax checks passed.

No source mascot/logo image changes, guest builds or payment claims were made.
This evidence supersedes the connector and fixed thank-you behavior in the prior
supporter-galaxy evidence; the remaining motion/accessibility limits still apply.

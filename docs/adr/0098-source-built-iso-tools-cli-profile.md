# ADR-0098: Omit the optional Tk frontend from the foundation ISO tools

- Date: 2026-11-07
- Status: Actual missing interpreter identified; corrected native package pending

Full-root integration review found `/usr/bin/xorriso-tcltk` with the actual
shebang `#!/usr/bin/wish`, while the foundation contains no Tk/wish. The prior
profile documented it as optional and untested, but installing an executable
with an unavailable interpreter conflicts with the unchanged image runtime
audit. Frozen libisoburn 1.5.8.pl02 Makefile.am installs this proof-of-concept
frontend unconditionally in bin_SCRIPTS alongside the unrelated CLI helper.

Ship the native ISO command-line tools and libraries required by the foundation.
Omit only xorriso-tcltk and its Info/man pages from package staging. Keep the
complete corresponding source archive and copyright notices. Package revision
becomes `1.5.8.pl02-2`; the frozen upstream source version is unchanged. Update
the exact native-version guard, not a permissive version pattern. H11 still
requires verified production media tools, and the full runtime audit is retained.

For this already-built target, recover from its own hash-verified accepted
archive after checking every installed payload entry. Preserve the predecessor
record/archive and prior successful recipe evidence. Repackage only the three
removed frontend files and the truthful profile document, then verify all
retained installed bytes and rerun the native library/ISO roundtrip checks.
No C/library rebuild or undocumented binary replacement is needed. Clean builds
apply the same stage helper before their initial package creation.

Alternatives: adding Tk/X11 solely for an unused ISO frontend expands foundation
scope and dependencies; whitelisting its missing interpreter weakens the image
audit; leaving an unusable command while only disclaiming it is avoidable.
This choice removes no PRD feature or test. The graphical installer remains B12
and is unrelated to this upstream disc-authoring frontend.

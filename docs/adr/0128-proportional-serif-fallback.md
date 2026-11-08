# ADR-0128: Unmodified proportional serif fallback

- Date: 2026-11-08
- Status: Accepted; owned native font and changed-input Pango qualification completed

With the six approved Adwaita50 fonts installed, native Fontconfig resolves serif
to Adwaita Mono. Browser/document serif text needs an actual proportional face.
Use the four original DejaVuSerif2.37 regular/bold/italic/bold-italic TTFs, named
by frozen BLFS13.1 x/TTF-and-OTF-fonts.html#dejavu-fonts. Preserve Adwaita Sans/Mono,
existing Fontconfig policy and user overrides; add no forced terminal settings.
This completes a font dependency, not a brand/logo/mascot redesign.

The [official download page](https://dejavu-fonts.github.io/Download.html) publishes
size5429777 and SHA256fa9ca4d13871dd122f61258a80d01751d603b4d3ee14095d65453b4e846e17d7
for dejavu-fonts-ttf-2.37.tar.bz2. Its official GitHub asset returned504; the
project's official SourceForge transport matched both size and digest. Freeze the
source before guest extraction. Do not generate or rename glyphs. Retain the
complete LICENSE: Bitstream/Arev copyright, trademark, renaming and sale conditions
plus the public-domain status of DejaVu's changes, outside Toddy's artwork grant.

The isolated data-only stage must byte-compare all four originals, verify family,
and enter the existing full-root owned package transaction. Generate native
Fontconfig caches separately from portable package contents, with a retained
manifest for final-image regeneration. Native postcheck must verify package
ownership, family/weight/slant, Latin/Portuguese/Cyrillic coverage, actual generic
fallbacks and a FreeType i/W advance comparison proving proportional spacing.
None of these gates has yet run. A changed installed font set then requires the
17 affected Pango drivers with unchanged library/test binaries, reusing unrelated
core/metric evidence. GUI/browser rendering and locale coverage remain separate
native product checks; do not claim CJK coverage from this font selection.

## Native outcome

Four original faces byte-identical in isolated stage; native owned install/post0/0
passed family/weight/slant, Latin/Portuguese/Cyrillic, ownership/cache and actual
FreeType proportional i/W advance checks. Generic defaults now resolve to
DejaVu Serif/Adwaita Sans/Adwaita Mono. The17 affected Pango drivers returned0
with all original binaries unchanged and eleven font hashes bound to evidence.
Other nine core passes and independent metric oracle reused; original upstream
golden failure remains visible. See B02-dejavu-fonts-install.json and
B02-pango-serif-fonts.json. Native GNOME/browser visual acceptance remains pending.

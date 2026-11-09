# ADR-0143: Recognize the frozen canonical DDS MIME type in Glycin configuration

Status: accepted; actual native DDS/color follow-up passed, owned promotion pending.

## Evidence and cause

The first real Glycin2.1.5 native7.1.8 run passed forced-BWRAP PNG/SVG pixel
decoding and malformed refusal, all8 selected encoding cases,4 editing cases,
1 memory-format case and10 of11 image cases. The original `color` case failed:
`UnknownImageFormat("image/vnd.ms-dds", ...)`. Preserve the original failure and
report SHA `e96b6024983854cff51331a0375545e148b36fee6d410c1d245b806ac3d5b7b8`.
Loader binary test programs contain zero cases; the upstream D-Bus API case is
ignored. The AVIF creator test and unsupported HEIF/AVIF/JXL formats are not passes.

The authenticated shared-mime-info2.5.1 source
`ea248ea157b7fa0165f4fe282c84919fa84c3f175553642f229c8f1ab7539128`,
`data/freedesktop.org.xml.in`, declares `image/vnd.ms-dds` with magic `DDS ` and
extension `.dds`; `image/x-dds` is its alias. Authenticated Glycin2.1.5 source
`6c09757ee906330a60b6705753aa56bca007ad219b95e6e3537510d41bc341c8`,
`glycin-loaders/glycin-image-rs/glycin-image-rs.conf`, registers only
`image/x-dds`. Its Cargo manifest already enables the DDS decoder. This is a
configuration compatibility gap between the frozen versions, not evidence that
the decoder or sandbox should be disabled or the foundation upgraded.

## Decision and qualification

Add exactly one canonical loader section for `image/vnd.ms-dds`, pointing at the
same existing DDS loader. Preserve the legacy name and every original entry.
`glycin_mime_compat.py` refuses a missing/different legacy entry, a preexisting
canonical entry and unexpected executable shape, then compares every original
parsed entry with the result. The initial config-only native follow-up reached the decoder but failed with
`RemoteError(UnsupportedImageFormat("image/vnd.ms-dds"))`. Its original failure
is retained in native-glycin-runtime-3. Source inspection then confirmed
`glycin-image-rs/src/main.rs` also matches only the legacy spelling.

Extend exactly that existing DDS match arm with the canonical spelling using
Rust pattern alternation. Both spellings execute the same decoder implementation.
Rebuild only glycin-image-rs offline from a private writable source copy; preserve
original immutable inputs/source/loader, compare every copied source file and
require only this one line to differ. Every staged file except the loader and
its configuration must remain byte-identical. No MIME database, security selector
or golden image assertion changes; no version upgrade or core rebuild.

Apply the same transformation to a private native runtime stage before upstream
test-prefix configuration, retaining before/after hashes. Rerun only the original
failed `color` case with the same original test executable and updated loader, preserving prior23 passing Rust
cases and native GI results bound to the full report/artifact hashes. A new
disposable cold overlay must verify the stopped earlier VM and unchanged backing.
If accepted, the owned native package must contain the exact corresponding
canonical configuration and exact natively tested updated loader; core, SVG loader
and original test binaries remain unchanged; constructor-only evidence still
does not authorize promotion. The original failed report remains visible.

This affects configured DDS availability only. It does not qualify GNOME,
hardware, omitted optional decoders or G2, and does not alter the owner's boundary:
complete all B02 acceptance, then pause before another story.

## Actual follow-up

Native4 passed DDS pixel/exif comparison after the one-arm source correction,
with only image-rs/config staged files changed. Its actual forced-bwrap PNG/SVG
GI/refusal consumer passed. The original color driver then exposed a separate
relative-image SVG fixture issue under our synthetic symlinked test root.
Native5 restored a real directory of byte-identical original image files and
passed the original color case unchanged, reusing23actual original Rust passes
and exact native4 candidate-stage hashes/GI proof. Preserve every earlier failure;
the linked-directory behavior remains a visible limitation. No tolerance, golden
image or sandbox change. Frozen probe payloads and all three qualification reports
were independently verified/imported; see B02-glycin-build.json.

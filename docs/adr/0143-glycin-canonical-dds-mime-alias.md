# ADR-0143: Recognize the frozen canonical DDS MIME type in Glycin configuration

Status: accepted for the selected Phase 2 decoder profile; native follow-up pending.

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
parsed entry with the result. No source, executable, MIME database, security
selector or golden image assertion changes.

Apply the same transformation to a private native runtime stage before upstream
test-prefix configuration, retaining before/after hashes. Rerun only the original
failed `color` case with the same executable, preserving prior23 passing Rust
cases and native GI results bound to the full report/artifact hashes. A new
disposable cold overlay must verify the stopped earlier VM and unchanged backing.
If accepted, the owned native package must contain the exact corresponding
canonical configuration and unchanged binaries; constructor-only evidence still
does not authorize promotion. The original failed report remains visible.

This affects configured DDS availability only. It does not qualify GNOME,
hardware, omitted optional decoders or G2, and does not alter the owner's boundary:
complete all B02 acceptance, then pause before another story.

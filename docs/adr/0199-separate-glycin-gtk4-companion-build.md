# ADR-0199 — Build the Glycin GTK4 companion against the existing owned core

Status: accepted · Date: 2026-11-10 · Story: B02

Nautilus50.2.2 requires glycin-gtk4-2. The frozen Glycin2.1.5 bundle contains
libglycin/libglycin-gtk4 API2.1.0. Its actual Meson contract explicitly supports
`libglycin=false`, `libglycin-gtk4=true` against installed glycin-2. Reuse owned
core2.1.5-1+toddy1/API2.1.0 and both qualified loaders; no accepted core/loader
rebuild, vendor update or broader loader profile. Build release/offline/locked,
GTK4/GI only, no loader/thumbnailer/Vala/docs/original Python suite. Use the upstream
supported `lto=false` option for this small bridge within measured scratch capacity.

Source archive SHA256
`6c09757ee906330a60b6705753aa56bca007ad219b95e6e3537510d41bc341c8`
remains the existing source lock. Before dispatch all436archive source files and
307vendor packages matched their authenticated manifests. The first own read-only
preflight lacked tomllib for the imported verifier; no job/receipt was created.
After that import correction, build1 completed0 in1m38s:78ELFs/five stage files,
GI namespace and shared symbol resolution passed. Those are compile/link results,
not real image conversion. The stage explicitly remains unpromotable.

Reuse existing Glycin scratch volume UUID1ae14c30-65f3-4e02-be0a-b257719455f2:
a distinct child directory/inode5538 bound at a distinct compiler work root.
Only this worker can write that child; accepted production/test directories remain
separate. No new filesystem, formatting, reserve reduction or duplicate source
extraction. Initial scratchfree954634240B, after build401514496B. Deterministic
monitor preserves128MiB scratch free, terminating only its own tracked compiler
group if reached. Target16GiB/host100GiB reserves remain. A supplementary dispatch
receipt records the exact actual recipe hash after adding this monitor; initial
volume preflight receipt is preserved. Cold recovery must first restore the
existing parent volume, then verify UUID/backing and mountpoint inodes before the
companion bind. `restore_glycin_gtk4_work.py NEW-RECEIPT` refuses a mounted target
or an existing receipt. It never recreates directories or filesystems.

[Build/input/capacity proof](../evidence/B02-glycin-gtk4-build.json) and raw SHA256
`e78fb61396916fb06bbabbecd81d3631f4671d07bb5b90fa44a1c2579896a2ea`.
A root-owned native test fixture contains only the five exact companion files,
plus recorded hashes of the installed core/loaders. Nothing has been installed.
Next use the NEW `native-glycin-gtk4-runtime-1` cold overlay, actual Toddy7.1.8
kernel, unprivileged BWRAP decoders and installed default loader paths, then prove
PNG/SVG to GDK textures, pixel-preserving PNG roundtrip, refusal and recovery.
Source for this native test is prepared, not yet executed. The broader original
Python test contains an unsandboxed-selector branch and is not substituted for
this explicit sandbox-preserving probe or reported as passed. No display/window,
GNOME, full B02 or physical acceptance is claimed by a headless memory texture.


## Verified native result and owned installation

The new cold context was executed once after commita66a22e. Actual native child
exited0/OOMfalse; backing identity unchanged, complete report SHA256
`40f5106816858bfe7e38dc690a59fb44c8dfa42f672686cac2b171c909deeeeb`.
Exact committed injected probe/consumer/bootstrap bytes were verified against both
recorded and actual Docker QEMU arguments. Actual7.1.8/Systemd/UID101/BWRAP with
owned installed default loader paths passed four PNG/SVG source pixels and
GDK-texture→PNG→decoded-pixel roundtrips, two malformed refusals/two recoveries.
All five staged companion files and installed core/loader inputs unchanged.
This supersedes the earlier unexecuted-test checkpoint above, without claiming
an actual display/window/widget or the broad original Python suite passed.

Parent builder restored only after the terminal child/backing checks. Existing
six filesystems/same Systemd read-only source/exact companion bind restored with
NEW receipts, no trim/format/recreation. Current builder boot
6af8df2c-a7d5-47e6-940d-4c78855e4e55. Do not replay either native test or restoration.
Native install/post0/0,817changedpaths/820owned entries, full frozen
source/vendor/Rust runtime notices retained. Five installed runtime/SDK files are
byte-identical to the native-tested stage; installed UID101 GI/shared symbols,
owned core resolution/pkg-config/APT0 passed. Reuse exact native proof rather than
retrying decoder sandboxing under the Ubuntu builder kernel. Core/loaders unchanged.
[Native/install proof](../evidence/B02-glycin-gtk4-install.json), package SHA256
`05de174923dce5293bac23772550189d5f3f718f83df7ff0f6f056b05f33cbe5`,
raw SHA256 `0abe95a4bb39bd7b20f274eabe1d668e87d4ea363b9465ddeb4d2e66cbd2395d`.
Companion frozen book page `general/glycin-gtk4.html` was inspected and confirms
the same separate-product switches and absence of a companion test suite; its
page hash is included in the proof. Default installed PNG/SVG loader integration
is now measured, superseding that limited pending item in earlier core evidence.
Broader image/desktop coverage remains unchanged.

Read-only Nautilus prerequisite refresh found all16required SDK modules; the
remaining build-tool prerequisite is blueprint-compiler>=0.19.0. No Nautilus input
or job exists. Resolve that pinned tool, then build the planned minimal Nautilus
profile and run its selected original headless checks before real GUI acceptance.

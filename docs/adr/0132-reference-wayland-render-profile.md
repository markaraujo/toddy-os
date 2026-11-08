# ADR-0132: First reference Wayland software render profile

- Date: 2026-11-08
- Status: Accepted; reference software Mesa owned install/post0/0

Build frozen Mesa26.1.7 for the reference guest's first working graphics path:
Wayland, EGL, GBM, GLES2/3, desktop OpenGL and llvmpipe/softpipe/virgl/svga.
Reuse native LLVM22.1.8 shared runtime/SDK, Mako1.4.1, PyYAML6.0.3, libdrm2.4.134
and qualified Wayland libraries. No compiler/foundation rebuild or version drift.
PyYAML is an explicitly pure-Python build tool; optional LibYAML accelerator is
absent. Its1283 original fixture cases and native safe parsing/emission/refusal
consumers passed, with the upstream boolean result asserted (the original
test_all.py entry point alone does not propagate failures).

This first profile disables GLX/Vulkan/OpenCL/VA/codec paths that are not needed
for the selected native Wayland render checkpoint. It does not qualify or remove
future essential-driver flows or physical GPU support. Hardware acceleration,
additional API/driver profiles and their source/compiler dependencies remain
pending actual qualification. Do not advertise them as available or close desktop,
driver, installer or G2 acceptance from software rendering alone. In particular,
Mesa's current Intel CLC and AMD LLVM requirements cannot be inferred from the
previously qualified CPU-only LLVM SDK. Record later affected additions explicitly.

The frozen book's xdemos patch is recommended for testing an Xorg installation;
this profile does not build Xorg/GLX demos. Require a real independent native
surfaceless EGL context, GLES shaders, triangle rasterization and navy RGBA pixel
readback using llvmpipe. This is executable graphics evidence, not a window,
GNOME interaction, hardware rendering or HTML mockup acceptance.

Use existing UID101/caps0/offline/read-only-input isolation. Keep all registered
upstream tests for this unqualified recipe, preserve full test/exit logs and
before/after compiled ELF hashes, account for actual upstream skips. Preflight
20GiB target free space (four GiB scratch above the16GiB reserve) and100GiB host
reserve; retain sources/packages/evidence. Native installation requires its own
verified stage, independent owned archive, legal notices, full-root transaction
and actual installed render consumer before runtime availability.


## Native outcome

All48 registered upstream drivers qualified:43 original passes retained, five
wrappers rerun after building only their two build_by_default:false dependencies.
Original --no-rebuild had omitted these tools; preserve job1 failure. First stage
completed in job2; consumer link then lacked indirect libgallium/libgbm lookup.
Consumer-only finish3 adds -rpath-link for link-time staging, with no persistent
RPATH/RUNPATH. Both original failures remain exit1. Source/tests/assertions were
unchanged; original1266 compiled ELFs and complete stage stayed identical.
Fresh recipe explicitly builds the two test dependencies and sets link-time path.

Actual staged and installed EGL1.5/GLES shader compilation, triangle rasterization
and readback returned RGBA0/32/64/255 using llvmpipe(LLVM22.1.8,256bits). Native
owned install/post0/0 in77.302s, archive169289ffb0a68159ec37fbcc8b9ef50db8f4d8c911a5bb2df65451bb0d48f121.
Source/version/package/ABI dependency audit and6876 retained named/header notices
in B02-mesa-build.json/install.json; raw bundle retained. No native GNOME/window,
physical GPU, Vulkan/GLX or final image acceptance follows from this profile.

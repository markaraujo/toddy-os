# ADR-0132: First reference Wayland software render profile

- Date: 2026-11-08
- Status: Accepted; native Mesa build/qualification pending

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

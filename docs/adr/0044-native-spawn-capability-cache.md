# ADR-0044: Detect native spawn capabilities after the frozen Glibc revert

- Date: 2026-11-06
- Status: Corrected package and native postcheck accepted

The complete ACL retest and Linux API/layout ownership passed. The installed
lfs-build-support 13.1-1 postcheck then correctly failed compiling the two
unsuffixed POSIX spawn directory actions. No successful marker was written.
The frozen LFS 13.1 chapter06/m4.html section 6.2 writes two cache answers yes
for the original Glibc 2.44 header-only aliases. However the already-frozen
Glibc upstream_fixes-3 patch 49 explicitly reverts those aliases. Native
spawn.h and exported libc symbols agree: the _np functions exist; the
unsuffixed aliases do not. This is an interaction between the selected book
bootstrap instructions and its selected maintenance overlay, not a missing
runtime package or a reason to silently change the frozen Glibc version.

Primary sources: frozen glibc-2.44-upstream_fixes-3.patch patch 49, original
and patched posix/spawn.h, posix/Versions, and
[upstream revert discussion](https://inbox.sourceware.org/libc-alpha/20260831161028.3062421-2-adhemerval.zanella@linaro.org/).
[Earlier Gnulib discussion](https://sourceware.org/pipermail/libc-alpha/2026-July/179255.html)
explains the original alias/workaround interaction. The local frozen inputs
and actual compile result take precedence over newer development interfaces.

Preserve original archive/record and failed runner evidence. Install the
book-derived support package as 13.1-2: retain exact original cross config in
its documentation, use a comment-only native config.site and let configure
measure capabilities. After accepted final Glibc, clean recipe environments
set CONFIG_SITE=/dev/null to avoid the earlier bootstrap cache even before
support-package ownership is finalized. Earlier cross/temporary recipes keep
their original book behavior. The support postcheck explicitly loads the
actual installed native site and requires both unsuffixed checks no and both
_np checks yes. It also compiles/runs real child working-directory actions,
not merely a no-op API initialization. All assertions must pass in the target.

Keeping false yes answers would poison future feature detection. Forcing no
answers would unnecessarily hardcode absence for future environments. Removing
the frozen Glibc maintenance patch or inventing ABI aliases changes runtime
scope without need. Automatic native detection is the smaller correction.
Original failed package/stage are preserved and no existing pass is relabeled.

Already-accepted Bison source has its own Gnulib wrapper calling the actual
_np symbol; installed Bison imports that valid GLIBC_2.29 symbol. Its unchanged
full tests passed, as did M4/Gettext and measured native Autotools build flow.
The full installed ELF audit and build flow must repeat after final closure;
these observations do not claim exhaustive absence of all latent defects.
This correction adds no permission restriction or product scope change.

Actual acceptance: lfs-build-support 13.1-2 archive SHA-256
1e8bbc7d4bb0ad0590682a27980e172d65f9d811caf30291b3521aaaac215dd7.
Same-step runner recipe/postcheck 0/0; log SHA-256
ae05d8fa5f0856b8a02af6fae7db695075b6f73cd93d8467a780cf8794993846.
Autoconf explicitly loaded the installed native site and detected no/no/yes/yes.
Separate real child runs proved path and descriptor directory actions. Original
13.1-1 archive/record/failed log remain preserved. H07 is not yet complete.

# ADR-0020: Use Findutils' supplied fixed regex implementation

- Status: Accepted; full retry and native regression passed
- Date: 2026-11-06
- Scope: H07 frozen Findutils 4.11.0 on Glibc 2.44

## Evidence and decision

The initial complete check failed only test-regex-el: three Greek sigma
fastmap mismatches. Its gnulib summary is 379 PASS/44 SKIP/one FAIL; the
separate find/xargs group reports 25 PASS/4 SKIP/zero FAIL. The package was not
installed and the runner recorded zero installed changes. The test itself
identifies Glibc bug 20381, verifies the real Greek single-byte locale and
compares all three sigma variants with/without a fastmap. Configure incorrectly
cached gl_cv_func_re_compile_pattern_working=yes.

The frozen archive already supplies Gnulib's corrected re_set_fastmap_icase
implementation in gl/lib/regcomp.c. Upstream Gnulib commit
acc1d91810195f62ce32c22d271fed3da74794bf subsequently added the missing Greek
probe to m4/regex.m4, making this case select that supplied replacement. Use
that measured configure result explicitly:
gl_cv_func_re_compile_pattern_working=no. Keep all source versions and tests
unchanged; no new library code or downloaded replacement is introduced.

Preserve the original tree/config/logs, rebuild the verified archive with the
corrected selection, repeat the entire unprivileged suite and require an
actual PASS (not SKIP) for test-regex-el. Native find must also match a final
sigma filename against uppercase sigma in the same Greek locale. Only then
install/accept the native package.

## Alternatives and consequences

Removing the locale/test, declaring an XFAIL or ignoring make's nonzero exit
would conceal the failure. Upgrading Findutils to bypass it violates the
frozen-source policy. A system-libc backport would affect the whole final base
and needs a separately justified change and critical retest. Selecting the
already supplied, source-fixed implementation is the narrow upstream-supported
correction; configuration changes require rebuilding the failed package.

This does not fix Glibc's implementation globally. Audit remaining regex
consumers before G1 and retain any measured residual limitation explicitly.
Do not claim general Greek case-fold correctness for unrelated programs from
Findutils' result. Full rebuilt suite passed, including an actual PASS for test-regex-el. Native
Greek final-sigma matching passed; dispatcher recipe/postcheck both exited zero.

## Primary sources

- Frozen LFS 13.1-systemd section 8.63 and SHA-pinned Findutils archive.
- Actual gl/m4/regex.m4, gl/lib/regcomp.c and gnulib-tests/test-regex-el.c
  read directly in the failed target tree.
- [Upstream Gnulib configure-probe correction](https://github.com/coreutils/gnulib/commit/acc1d91810195f62ce32c22d271fed3da74794bf), including its reference to the supplied runtime fix.
- [Glibc issue 20381](https://sourceware.org/bugzilla/show_bug.cgi?id=20381):
  the tracker page was access-denied; diagnosis uses the accessible primary
  upstream code/commit and the actual reproducer, not an invented tracker status.

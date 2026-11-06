# ADR-0034: Native APT profile and acquisition sandbox

- Date: 2026-11-06
- Status: Build/test profile selected; acceptance pending

Build frozen APT 3.0.4 with native Dpkg/Perl/CMake/Triehash and required libraries.
Use GNUInstallDirs with /usr/lib, /usr/libexec, /etc and /var. Select an explicit
Toddy vendor configuration; do not import Debian/Ubuntu repositories or keys.
Keep translations and build the complete GTest suite. Full documentation needs
additional DocBook/XSL tooling; initially WITH_DOC=OFF, retained source README,
COPYING and configuration provide provenance, not a claim of generated manuals.

Build libseccomp 2.6.1 from frozen BLFS 13.1 plus Which 2.25 for its suite. Both
archives match book MD5; SHA-256 recorded in supplemental lock. Run complete
make check and installed native kernel-filter probe. Enable APT's real seccomp
integration rather than silently using an optional-library omission. Use an
unprivileged locked _apt account for downloads. Keep scoped Signed-By keyrings;
no apt-key/keyring URI, trusted=yes or unauthenticated bypass.

APT runtime gpgv is supplied by accepted native GnuPG, as permitted by source
Debian control's sqv | gpgv dependency. Actual upstream integration framework
also requires Sequoia sq, fakeroot, stunnel and other optional test tools. This
is distinct from the configured CTest suite. Retain any invocation failures and
report coverage accurately; do not patch away assertions or claim unavailable
integration cases passed. Native Toddy repository acceptance must independently
exercise real signatures, dependency ordering, conffile upgrade, tampered index/
payload and unknown-key rejection plus recovery using disposable package roots.
No release gate follows from only CTest or apt --version.

Primary sources: frozen APT 3.0.4 CMakeLists.txt, vendor/README,
methods/CMakeLists.txt, debian/control, debian/tests/control and test/integration/
framework; BLFS 13.1-systemd general/libseccomp.html and general/which.html.
Official upstream: https://github.com/seccomp/libseccomp/releases/tag/v2.6.1,
https://ftp.gnu.org/gnu/which/.

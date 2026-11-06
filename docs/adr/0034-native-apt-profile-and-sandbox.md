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

The prepared repository postcheck also exercises native APT HTTPS acquisition
and installation from a loopback-only Python TLS server. A one-day disposable
certificate has only DNS:localhost SAN; trust is scoped through command-only
Acquire::https::CAInfo. Keep Verify-Peer/Verify-Host defaults enabled. Clear only
own fixture indexes/cache before fetches; require actual successful payload
GET and install. Then require exit 100 with certificate-verification error for
normal-system-CA rejection and trusted-CA/wrong-host rejection, restore successful
update, purge and verify main package database unchanged. Server drops to tester
after loading its key and stops before fixture/key cleanup; no trust/key/service
is installed system-wide.

A focused native Python/OpenSSL server-fixture preflight passed positive TLS
and rejected unknown CA (verify code 18) and wrong IP name (64). Raw log
.local/logs/h07-apt-https-server-preflight.log SHA-256 db270c2afb9b11b6effbcb4d5f026d3880061f3373021df6fabc6bfc0361bc85.
That preflight does not claim native APT transport acceptance; the complete APT
postcheck remains mandatory after its actual build. Configuration semantics
come from frozen APT 3.0.4 doc/apt-transport-https.1.xml and methods/connect.cc,
including enabled peer/name verification and scoped CaInfo loading.

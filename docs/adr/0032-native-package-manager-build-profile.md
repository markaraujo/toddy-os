# ADR-0032: Build native package-manager integration without replacing state

- Status: Recipes prepared; native build/test acceptance pending
- Date: 2026-11-06
- Scope: Frozen Dpkg 1.22.22 and maintained Berkeley DB 5.3.28+dfsg2-12

Dpkg's source configure supports perllibdir; use the actual native Perl Config
vendorlib path so installed Perl frontends load their modules on the LFS layout.
Keep the intended private static libdpkg; upstream explicitly does not promise
shared-library ABI stability. Enable the already built compression libraries,
run the complete unprivileged upstream suite and retain configured skip reasons.

Exclude generated status/available/lock files from staged /var/lib/dpkg before
packaging. Never overwrite the populated bootstrap ownership database with
empty DESTDIR state. Keep static configuration as conffiles. Native postchecks
must exercise the actual installed dpkg-deb/dpkg/query/architecture programs:
create/install a disposable package, upgrade while preserving a changed conffile,
reject a conflicting package, remove/purge and prove the main database hash is
unchanged by those isolated operations. Build-host dpkg remains bootstrap
infrastructure until separately verified native packaging dispatch is implemented.

APT's actual FindBerkeley.cmake requires the C db library/header, not C++/Java/
SQL/DBM bindings. Build the C profile only, avoiding duplicate GDBM compatibility
interfaces. Apply all 19 frozen maintained patches strictly; the independent
source-only preflight passed every patch with zero fuzz. Regenerate upstream
autotools with native Libtool/Autoconf and validate generated configuration before
building. Debian build/maintainer scripts are never executed or installed; only
patch data/copyright/changelog are extracted from that archive.

Use -std=gnu17 as the maintained Debian source recipe specifies, with native
GCC 16.2. Build a test configuration with Tcl/internal test APIs, run CuTest and
the complete upstream standard Tcl regression suite, then build the production
configuration with internal test APIs/Tcl disabled. This follows the source
maintainer's two-build pattern. Require upstream Regression Tests Succeeded,
completion marker and absence of FAIL; Tcl's process exit alone is insufficient.
Preserve raw ALL.OUT and all diagnostics. No configured test is removed.

Native production checks must prove exact version, actual B-tree transaction
commit, aborted update, process close/reopen and persistent correct value using
the installed library. No complete BDB/APT/repository acceptance follows from
source downloads, host-side patch application or prepared scripts. Native signed
APT repository/solver/tamper/update/recovery tests remain required before H07
closure and G1.

Sources: actual frozen Dpkg configure.ac/m4/dpkg-progs.m4, native Perl recipe,
APT CMake/FindBerkeley.cmake, maintained DB debian/rules and upstream
 test/c/README/test/tcl/test.tcl. Rules were read as evidence, not executed.

### Authenticated FIFO fixtures

First Dpkg extraction was refused before compilation at its three official FIFO
fixtures: tests/t-unpack-fifo/pkg-fifo/test-fifo and
tests/t-unpack-hardlink/pkg-hardlink/test-fifo-link{0,1}. Allow only those exact
FIFOs for dpkg_1.22.22.tar.xz after frozen SHA-256 verification. Preserve standard
path/mode/ownership filtering; reject all other special entries. Prevalidate
all members before extraction. Regression tests cover wrong archives, unexpected
FIFOs/devices and escaping paths. Original partial tree/failure retained.

### Actual native build feedback

Dpkg full configured suite and native install/upgrade/conffile/conflict/remove/
purge postconditions passed; log SHA-256
cc609c7462e4b56102228abee78df0aa905cf4622bd1b142771f8769590b65c1.
The first DB test build failed because upstream Tcl test bindings unconditionally
reference DBM/compat185 types/functions. Enable those interfaces in the disposable
test build only, as the maintained two-build default permits. Production retains
disabled DBM/compat185 and no conflicting GDBM interfaces. No tests/source are
removed or modified. Preserve failed tree/log and rebuild from verified inputs.

The next native link exposed the maintained versioned-symbols patch's reliance
on non-PIC .o files: it strips .libs/ from Libtool pic_object paths before nm.
With --disable-static, those files do not exist and the generated global symbol
list is empty; GNU ld correctly rejects it. Enable static object generation in
both builds, matching the maintained source default, then exclude .a/.la files
from the staged production package. Keep symbol versioning and full tests; no
patch or exported ABI is removed. Preserve failed tree/log before fresh retry.

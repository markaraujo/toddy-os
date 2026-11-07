# ADR-0068: Restore the missing Berkeley DB native test-process interface

- Date: 2026-11-07
- Status: First three native cases passed; complete group validation pending
- Scope: Test-only process adapter; no production database changes

ADR-0067 established that the frozen 5.3.28 archive and its upstream release
tree omit test/repmgr/db_repsite.cpp. Merely enabling C++ cannot build an absent
source. Removing multi_repmgr would discard eleven published regression cases.
Neither changing the frozen database version nor synthesizing passing replies
is an acceptable substitute for exercising this library.

Implement scripts/build/h07/db_repsite.c against the actual native 5.3.28 C API
and the command protocol consumed by frozen test/tcl/reputils.tcl and
repmgr100, 101, 102, 105, 106, 107, 108, 109, 110, 111 and 112. The adapter
opens real environments/databases, starts replication-manager threads, writes
transactions, enumerates actual connected sites and closes real handles. It
does not interpret Tcl assertions or know a test's expected database contents.
Remote peer/bootstrap flags follow the frozen lang/tcl/tcl_rep.c mapping.
DB_REP_IGNORE is returned from the actual API for subordinate listeners;
repmgr102 explicitly checks it before and after genuine process death/failchk.
Ordinary process-death signals retain their default abrupt behavior.

The line protocol separates native diagnostics from replies, rejects malformed
commands and propagates native operation failures. The helper refuses root
execution and is used only by the disposable tester account. It must never be
installed in the production package. Its build uses the frozen native db.h and
libdb-5.3.so, with warnings treated as errors. The production C-only profile is
unchanged. This is an independently implemented adapter, not a recovered or
upstream-approved copy of the missing source.

The first private native probe compiled with -O2 -std=gnu17 -Wall -Wextra
-Werror and ran the three unchanged cases repmgr100, repmgr101 and repmgr102.
All three passed, including replicated data visibility, subordinate connections,
abrupt process death and actual failchk takeover. Captured exit 0 and sentinel
MULTIPROC_FIRST_THREE_PASSED; log SHA-256
7a1fc4311289856a5578789b5325871e9c6a82e2ab3328f4de819d273c638765.
Adapter source SHA-256
827f84ea724f12d6c91c5b215026e0e771a896423b67654690bd85ffaf08735c;
native executable SHA-256
4649eda06c59a36dff11bf0a4002ef2721e4b69afebd4a79cfefc03cf0afab2d.

A separate complete multi_repmgr run now uses the committed focused Tcl entry
point, all eleven original cases and their unchanged assertions. Its private
build-multiproc directory and network namespace avoid sharing TESTDIR or ports
with other_repmgr and the original standard suite. The first successful fixture
was preserved as first-three.TESTDIR before launching the full group. The
complete run must pass before integrating the helper into fresh/recovery builds;
all-suite acceptance remains separately mandatory. Three passing cases are not
eleven passing cases, a completed standard suite or an accepted package.

The sanitized 00:58 UTC observation is
.local/logs/h07-repmgr-adapter-progress.json, SHA-256
619f31e3d14dde3c6e7936663eb5b99cdcd86c75c5677e5e4d9982b1e5d26ece.
It also records the original standard suite progressing through Rep020 with the
same two FAIL lines. That run cannot authorize production installation or APT.

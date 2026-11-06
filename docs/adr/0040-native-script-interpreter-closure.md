# ADR-0040: Resolve measured native script interpreter requirements

- Date: 2026-11-06
- Status: Source/profile selected; native corrections pending

Read-only audit measured 380 interpreter edges and 275 undeclared/absent findings
in the 101-package target. Most are real Bash/env/Perl/Python dependencies omitted
from initial book-order metadata. Derive and record direct interpreter-provider
edges alongside ELF providers; final metadata audit must have no unresolved
shebang. This does not establish arbitrary internal tool/data/GUI dependencies.

Three files request unversioned python: Python 3's rot_13 module, DBus's example
and Vim's demoserver. Vim explicitly supports Python 3 via socketserver fallback;
compile both examples with the actual native interpreter and run rot_13. Provide
/usr/bin/python -> python3 as owned Python +toddy1 package metadata, preserving
all binary/source versions. PEP 394 explicitly permits distributors to choose
Python 3 for python. Do not install obsolete Python 2 or rewrite upstream tests.
The Python-only metadata slice runs before full closure, already adding its
measured Bash/Coreutils dependencies; later upgrade skips only verified version.
The DBus example's optional dbus Python module is not claimed available yet.

Vim's installed vim132 really uses /bin/csh; do not pretend it is a POSIX shell
script or hide the missing interpreter. Freeze/build Tcsh 6.24.16 from BLFS 13.1
chapter 7. Official archive matches book MD5 448f53f12544abb627c9f078373b8ff5;
SHA-256 4208cf4630fb64d91d81987f854f9570a5a0e8a001a92827def37d0ed8f37364.
No independent signature claim. Run complete make check, install csh/man aliases
through merged-/usr, and prove actual arrays/loops/child-exit status as native
csh. Registration in generated /etc/shells belongs to H08. No claim of physical
VT-100 132-column behavior follows from parser checks.

Primary sources: frozen BLFS 13.1 postlfs/tcsh.html; actual installed consumer
scripts; https://astron.com/pub/tcsh/tcsh-6.24.16.tar.gz;
https://peps.python.org/pep-0394/. Raw audit:
.local/logs/h07-script-interpreters-101.json. No correction is claimed accepted
before actual native recipe/postcheck evidence.

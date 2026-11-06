#!/usr/bin/env python3
"""Exercise installed native Autotools, shared-library build and staged install."""
import json
import subprocess

PROGRAM = r'''set -euo pipefail
fixture=$(mktemp -d /tmp/toddy-native-build-flow.XXXXXX)
trap 'rm -rf "$fixture"' EXIT
cd "$fixture"
cat > configure.ac <<'EOF'
AC_INIT([toddy-native-build-flow],[1])
AM_INIT_AUTOMAKE([foreign])
AC_CONFIG_SRCDIR([answer.c])
AC_PROG_CC
LT_INIT
AC_CONFIG_FILES([Makefile])
AC_OUTPUT
EOF
cat > Makefile.am <<'EOF'
lib_LTLIBRARIES = libtoddy.la
libtoddy_la_SOURCES = answer.c
libtoddy_la_LDFLAGS = -version-info 0:0:0
check_PROGRAMS = probe
TESTS = probe
probe_SOURCES = probe.c
probe_LDADD = libtoddy.la
EOF
printf 'int answer(void) { return 42; }\n' > answer.c
printf 'extern int answer(void); int main(void) { return answer() != 42; }\n' > probe.c
autoreconf --force --install --verbose
./configure --prefix=/usr --disable-static
make -j2
make -j2 check
# Libtool's wrapper must execute against the just-built native shared object.
./probe
make DESTDIR="$fixture/dest" install
test -s dest/usr/lib/libtoddy.so.0.0.0
readelf -h dest/usr/lib/libtoddy.so.0.0.0
test -L dest/usr/lib/libtoddy.so
printf 'Native Autotools shared library, test wrapper and staged install passed\n'
'''


def main():
    subprocess.run(['bash', '-c', 'source /opt/toddy-build/scripts/build/target.sh; guard_target'], check=True)
    result = subprocess.run(['chroot', '/mnt/lfs', '/usr/bin/env', '-i',
                             'HOME=/root', 'PATH=/usr/bin:/usr/sbin', 'LC_ALL=C',
                             '/bin/bash', '-s'], input=PROGRAM, text=True, capture_output=True)
    report = {'scope': 'Native Autoconf/Automake/Libtool/M4/Make/GCC/Binutils shared-library integration; temporary fixture only',
              'exit': result.returncode, 'passed': result.returncode == 0,
              'stdout': result.stdout, 'stderr': result.stderr,
              'limitations': ['Not an exhaustive internal tool/data/dlopen dependency audit or native boot test.']}
    print(json.dumps(report, indent=2))
    if result.returncode:
        raise SystemExit(result.returncode)


if __name__ == '__main__':
    main()

#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $(dpkg-query --admindir="$LFS/var/lib/dpkg" -W -f='${Status}' ncurses) == 'install ok installed' ]]
chroot_run <<'INNER'
set -euo pipefail
pkg-config --modversion ncursesw | grep -E '^6\.6'
infocmp xterm > /tmp/toddy-terminfo
# Upstream test/README supplies standalone examples. Run its automatic
# setupterm error/success matrix after installation, as required by the book.
cd /sources/ncurses-6.6/test
./configure --with-ncursesw
make test_setupterm
mkdir -p /sources/evidence/h07-ncurses
./test_setupterm -a > /sources/evidence/h07-ncurses/setupterm.log
cat /sources/evidence/h07-ncurses/setupterm.log
[[ $(grep -c '^OK ' /sources/evidence/h07-ncurses/setupterm.log) == 4 ]]
! grep '^ERR' /sources/evidence/h07-ncurses/setupterm.log
cat > /tmp/toddy-curses.c <<'C'
#include <curses.h>
#include <stdio.h>
int main(void) {
 FILE *out=tmpfile(), *in=fopen("/dev/null","r");
 if (!out || !in) return 1;
 SCREEN *screen=newterm("xterm",out,in);
 if (!screen) return 2;
 if (addstr("CURSES_OK")==ERR || refresh()==ERR) return 3;
 endwin(); delscreen(screen);
 if (ftell(out)<=0) return 4;
 fclose(out); fclose(in); return 0;
}
C
gcc /tmp/toddy-curses.c $(pkg-config --cflags --libs ncursesw) -o /tmp/toddy-curses
/tmp/toddy-curses
rm /tmp/toddy-curses{,.c} /tmp/toddy-terminfo
INNER

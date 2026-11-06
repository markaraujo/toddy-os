#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $(dpkg-query --admindir="$LFS/var/lib/dpkg" -W -f='${Status}' mpdecimal) == 'install ok installed' ]]
chroot_run <<'INNER'
set -euo pipefail
cat > /tmp/toddy-decimal.c <<'C'
#include <mpdecimal.h>
#include <string.h>
#include <stdlib.h>
int main(void) { mpd_context_t c; mpd_defaultcontext(&c); uint32_t s=0; mpd_t *a=mpd_new(&c),*b=mpd_new(&c),*r=mpd_new(&c); mpd_qset_string(a,"0.1",&c,&s); mpd_qset_string(b,"0.2",&c,&s); mpd_qadd(r,a,b,&c,&s); char *v=mpd_to_sci(r,1); int ok=!s&&!strcmp(v,"0.3"); free(v); mpd_del(a); mpd_del(b); mpd_del(r); return !ok; }
C
cc /tmp/toddy-decimal.c -lmpdec -o /tmp/toddy-decimal
/tmp/toddy-decimal
rm /tmp/toddy-decimal{,.c}
INNER

#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $(dpkg-query --admindir="$LFS/var/lib/dpkg" -W -f='${Status}' gdbm) == 'install ok installed' ]]
chroot_run <<'INNER'
set -euo pipefail
cat > /tmp/toddy-gdbm.c <<'C'
#include <gdbm.h>
#include <string.h>
int main(void) { GDBM_FILE db=gdbm_open("/tmp/toddy-gdbm.db",0,GDBM_NEWDB,0600,0); if(!db) return 1; datum k={"key",3},v={"value",5}; if(gdbm_store(db,k,v,GDBM_REPLACE)) return 2; datum r=gdbm_fetch(db,k); int ok=r.dsize==5 && !memcmp(r.dptr,"value",5); gdbm_close(db); return !ok; }
C
cc /tmp/toddy-gdbm.c -lgdbm -o /tmp/toddy-gdbm
/tmp/toddy-gdbm
rm /tmp/toddy-gdbm{,.c,.db}
INNER

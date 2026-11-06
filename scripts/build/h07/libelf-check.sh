#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $(dpkg-query --admindir="$LFS/var/lib/dpkg" -W -f='${Status}' libelf) == 'install ok installed' ]]
chroot_run <<'INNER'
set -euo pipefail
cat > /tmp/toddy-elf.c <<'C'
#include <libelf.h>
#include <fcntl.h>
#include <unistd.h>
int main(void) { if(elf_version(EV_CURRENT)==EV_NONE) return 1; int fd=open("/usr/bin/cc",O_RDONLY); if(fd<0) return 2; Elf *e=elf_begin(fd,ELF_C_READ,0); if(!e || elf_kind(e)!=ELF_K_ELF) return 3; elf_end(e); close(fd); return 0; }
C
cc /tmp/toddy-elf.c -lelf -o /tmp/toddy-elf
/tmp/toddy-elf
rm /tmp/toddy-elf{,.c}
INNER

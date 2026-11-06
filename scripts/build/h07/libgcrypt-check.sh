#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $(dpkg-query --admindir="$LFS/var/lib/dpkg" -W -f='${Status}' libgcrypt) == 'install ok installed' ]]
chroot_run <<'INNER'
set -euo pipefail
cat > /tmp/toddy-gcrypt.c <<'C'
#include <gcrypt.h>
#include <string.h>
int main(void) {unsigned char digest[32];const unsigned char expected[32]={0xba,0x78,0x16,0xbf,0x8f,0x01,0xcf,0xea,0x41,0x41,0x40,0xde,0x5d,0xae,0x22,0x23,0xb0,0x03,0x61,0xa3,0x96,0x17,0x7a,0x9c,0xb4,0x10,0xff,0x61,0xf2,0x00,0x15,0xad};if(!gcry_check_version("1.12.4"))return 1;gcry_md_hash_buffer(GCRY_MD_SHA256,digest,"abc",3);return memcmp(digest,expected,32);}
C
cc /tmp/toddy-gcrypt.c -lgcrypt -o /tmp/toddy-gcrypt
/tmp/toddy-gcrypt
rm /tmp/toddy-gcrypt{,.c}
INNER

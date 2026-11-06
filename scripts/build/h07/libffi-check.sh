#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $(dpkg-query --admindir="$LFS/var/lib/dpkg" -W -f='${Status}' libffi) == 'install ok installed' ]]
chroot_run <<'INNER'
set -euo pipefail
cat > /tmp/toddy-ffi.c <<'C'
#include <ffi.h>
static int add(int x,int y) { return x+y; }
int main(void) { ffi_cif cif; ffi_type *types[]={&ffi_type_sint,&ffi_type_sint}; int a=20,b=22; ffi_arg result=0; void *values[]={&a,&b}; if(ffi_prep_cif(&cif,FFI_DEFAULT_ABI,2,&ffi_type_sint,types)!=FFI_OK) return 1; ffi_call(&cif,FFI_FN(add),&result,values); return result!=42; }
C
cc /tmp/toddy-ffi.c -lffi -o /tmp/toddy-ffi
/tmp/toddy-ffi
rm /tmp/toddy-ffi{,.c}
INNER

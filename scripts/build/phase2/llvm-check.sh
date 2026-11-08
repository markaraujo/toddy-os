#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/h06/common.sh
chroot_run <<'NATIVE'
set -euo pipefail
[[ $(llvm-config --version) == 22.1.8 ]]
clang --version | grep -F 'clang version 22.1.8'
[[ $(llvm-config --link-shared --shared-mode core orcjit native) == shared ]]
[[ $(dpkg-query -W -f='${Status}' llvm) == 'install ok installed' ]]
dpkg-query -W -f='${Conffiles}' llvm | grep -F ' /etc/clang/clang.cfg '
test -z "$(dpkg --audit)"
apt-get check
work=$(mktemp -d /tmp/toddy-llvm-consumer.XXXXXX)
trap 'rm -rf "$work"' EXIT
cat > "$work/proof.cpp" <<'CPP'
#include <numeric>
#include <vector>
#include <iostream>
int main() {
    std::vector<int> values={1,2,3};
    if (std::accumulate(values.begin(),values.end(),0)!=6) return 1;
    std::cout << "toddy-native-llvm\n";
    return 0;
}
CPP
clang++ -O2 -Wall -Werror "$work/proof.cpp" -o "$work/proof"
[[ $("$work/proof") == toddy-native-llvm ]]
readelf -h "$work/proof" | grep -E 'Type:.*DYN'
cat > "$work/canary.c" <<'C'
void external_sink(char *);
int proof(void) { char buffer[64];external_sink(buffer);return buffer[0]; }
C
clang -O0 -c "$work/canary.c" -o "$work/canary.o"
readelf -Ws "$work/canary.o" | grep -F '__stack_chk_fail'
cat > "$work/ir.ll" <<'IR'
define i32 @main() {
  %value = add i32 40, 2
  %ok = icmp eq i32 %value, 42
  %status = select i1 %ok, i32 0, i32 1
  ret i32 %status
}
IR
lli --jit-kind=orc "$work/ir.ll"
printf '%s\n' 'CHECK: toddy-native-llvm' > "$work/check.txt"
printf '%s\n' 'toddy-native-llvm' | FileCheck "$work/check.txt"
cat > "$work/clang-api.c" <<'C'
#include <clang-c/Index.h>
#include <string.h>
int main(void) {
    const char *code="int main(void) { return 0; }";
    struct CXUnsavedFile file={"proof.c",code,strlen(code)};
    CXTranslationUnit unit=NULL;CXIndex index=clang_createIndex(0,0);
    CXString version=clang_getClangVersion();
    if (!strstr(clang_getCString(version),"22.1.8")) return 1;
    clang_disposeString(version);
    if (clang_parseTranslationUnit2(index,file.Filename,NULL,0,&file,1,CXTranslationUnit_None,&unit)!=CXError_Success || !unit) return 2;
    if (clang_getNumDiagnostics(unit)!=0) return 3;
    clang_disposeTranslationUnit(unit);clang_disposeIndex(index);return 0;
}
C
cc "$work/clang-api.c" -lclang -o "$work/clang-api"
"$work/clang-api"
NATIVE

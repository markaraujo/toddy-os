#!/bin/bash
# ADR0121: compiler phase only. Tests/stage/install require separate receipts.
set -euo pipefail
[[ $(id -u) == 101 && -d /src/llvm && -d /src/clang && -d /dev/shm ]]
ulimit -c 0
python3 - <<'SPACE'
import os
s=os.statvfs('/build');assert s.f_bavail*s.f_frsize>=30*1024**3,'Need30GiB free before native LLVM compile; preserve16GiB reserve'
SPACE
cmake -S /src/llvm -B /build/compile -G Ninja \
    -DCMAKE_C_COMPILER=gcc -DCMAKE_CXX_COMPILER=g++ \
    -DCMAKE_INSTALL_PREFIX=/usr -DCMAKE_INSTALL_LIBDIR=lib \
    -DCMAKE_SKIP_INSTALL_RPATH=ON -DCMAKE_BUILD_TYPE=Release \
    -DLLVM_ENABLE_FFI=ON -DLLVM_BUILD_LLVM_DYLIB=ON -DLLVM_LINK_LLVM_DYLIB=ON \
    -DLLVM_ENABLE_RTTI=ON '-DLLVM_TARGETS_TO_BUILD=X86;AMDGPU' \
    -DLLVM_ENABLE_PROJECTS=clang -DLLVM_ENABLE_RUNTIMES= \
    -DLLVM_BINUTILS_INCDIR=/usr/include -DLLVM_INCLUDE_BENCHMARKS=OFF \
    -DLLVM_INCLUDE_EXAMPLES=OFF -DLLVM_INCLUDE_DOCS=OFF -DLLVM_BUILD_DOCS=OFF \
    -DLLVM_INCLUDE_TESTS=ON -DLLVM_BUILD_TESTS=OFF \
    -DLLVM_ENABLE_CURL=OFF -DLLVM_ENABLE_HTTPLIB=OFF -DLLVM_ENABLE_LIBXML2=OFF \
    -DLLVM_ENABLE_ZLIB=ON -DLLVM_ENABLE_ZSTD=ON -DLLVM_ENABLE_TERMINFO=OFF \
    -DLLVM_PARALLEL_COMPILE_JOBS=4 -DLLVM_PARALLEL_LINK_JOBS=1 \
    -DCLANG_DEFAULT_PIE_ON_LINUX=ON -DCLANG_CONFIG_FILE_SYSTEM_DIR=/etc/clang \
    -Wno-dev
ninja -C /build/compile -j4
[[ -x /build/compile/bin/clang && -x /build/compile/bin/FileCheck ]]
[[ $(/build/compile/bin/llvm-config --version) == 22.1.8 ]]
python3 - <<'RESULT'
from pathlib import Path
import json,hashlib,subprocess,os
base=Path('/build/compile')
version=subprocess.run([str(base/'bin/clang'),'--version'],capture_output=True,text=True,check=True).stdout
assert 'clang version 22.1.8' in version
names=subprocess.run([str(base/'bin/llvm-config'),'--targets-built'],capture_output=True,text=True,check=True).stdout.split()
assert set(names)=={'X86','AMDGPU'}
s=os.statvfs('/build')
Path('/build/compile-result.json').write_text(json.dumps({'scope':'native LLVM/Clang compile only; no test/stage/package acceptance','version':'22.1.8','targets':names,'clang_version':version.splitlines()[0],'cmake_cache_sha256':hashlib.sha256((base/'CMakeCache.txt').read_bytes()).hexdigest(),'free_bytes_after_compile':s.f_bavail*s.f_frsize,'next':'Required native compiler/JIT validation and verified stage per ADR0121'},indent=2)+'\n')
RESULT

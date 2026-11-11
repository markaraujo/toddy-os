#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 ]]
suffix=
if [[ ${1:-} == --readable-source-correction ]]; then
    [[ $# == 1 && -f /build/compile/Makefile && ! -s /build/compile/Makefile ]]
    grep -q 'No targets' /build/compile.log
    suffix=-readable-source
else
    [[ $# == 0 ]]
fi
[[ ! -e /build/compile$suffix ]]
ulimit -c 0
mkdir /build/compile$suffix
cd /build/compile$suffix
# BLFS13.1-systemd general/nasm.html; source3.02, unchanged configure recipe.
/src/configure --prefix=/usr > /build/configure$suffix.log 2>&1
make -j6 > /build/compile$suffix.log 2>&1
make DESTDIR=/stage install > /build/stage$suffix.log 2>&1
/stage/usr/bin/nasm -v | tee /build/nasm-version.txt
grep -q 'NASM version 3.02' /build/nasm-version.txt
cat > /build/probe.asm <<'ASM'
bits 64
global _start
section .text
_start:
    mov eax, 60
    mov edi, 42
    syscall
ASM
/stage/usr/bin/nasm -f elf64 /build/probe.asm -o /build/probe.o
ld /build/probe.o -o /build/probe
set +e
/build/probe
result=$?
set -e
[[ $result == 42 ]]
/stage/usr/bin/nasm -f bin /build/probe.asm -o /build/probe.bin
/stage/usr/bin/ndisasm -b 64 /build/probe.bin > /build/disassembly.txt
python3 - <<'PY'
from pathlib import Path
import hashlib,json
binary=Path('/build/probe.bin').read_bytes()
assert binary==bytes.fromhex('b83c000000bf2a0000000f05')
text=Path('/build/disassembly.txt').read_text()
assert 'mov eax,0x3c' in text and 'mov edi,0x2a' in text and 'syscall' in text
files={str(p.relative_to('/stage')):hashlib.sha256(p.read_bytes()).hexdigest() for p in Path('/stage').rglob('*') if p.is_file() and not p.is_symlink()}
assert 'usr/bin/nasm' in files and 'usr/bin/ndisasm' in files
Path('/build/result.json').write_text(json.dumps({'state':'stage-qualified','source_version':'3.02','configure_compile_stage_exit':0,'assembler_link_execute_exit':42,'machine_bytes_exact':True,'disassembler_positive_control':True,'stage_files':files,'scope':'Private compiler tool only; not installed in OS or native package acceptance. Frozen book describes no upstream test suite.'},indent=2)+'\n')
PY

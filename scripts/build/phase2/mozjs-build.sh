#!/bin/bash
# Frozen BLFS13.1 SpiderMonkey140.14 compile/stage only; critical suites follow.
set -euo pipefail
[[ $(id -u) == 101 && -f /src/project/js/src/configure && -d /stage ]]
mkdir /build/compile /build/cargo-home
export MOZBUILD_STATE_PATH=/build/mozbuild CARGO_HOME=/build/cargo-home
export CARGO_NET_OFFLINE=true CARGO_BUILD_JOBS=4 CARGO_INCREMENTAL=0
export PYTHONDONTWRITEBYTECODE=1 MOZ_NOSPAM=1
cd /build/compile
/src/project/js/src/configure --prefix=/usr --disable-debug-symbols \
    --disable-jemalloc --enable-readline --enable-rust-simd --with-intl-api \
    --with-system-icu --with-system-zlib > /build/configure.log 2>&1
printf '0\n' > /build/configure.exit
make -j4 > /build/compile.log 2>&1
printf '0\n' > /build/compile.exit
make DESTDIR=/stage install > /build/install-stage.log 2>&1
printf '0\n' > /build/install-stage.exit
python3 - <<'PY'
from pathlib import Path
import hashlib,json,os,subprocess
root=Path('/stage');archive=root/'usr/lib/libjs_static.ajs'
assert archive.is_file() and not archive.is_symlink()
omitted={'path':str(archive.relative_to(root)),'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'reason':'Frozen BLFS13.1 explicitly omits static archive from runtime stage'}
archive.unlink()
config=root/'usr/bin/js140-config';before=config.read_bytes();lines=before.splitlines(keepends=True)
removed=[x.decode() for x in lines if b'@NSPR_CFLAGS@' in x];assert removed
config.write_bytes(b''.join(x for x in lines if b'@NSPR_CFLAGS@' not in x))
header=root/'usr/include/mozjs-140/js-config.h';before_header=header.read_bytes();lines=before_header.splitlines(keepends=True);assert b'#define XP_UNIX' not in before_header
header.write_bytes(b''.join(lines[:-1])+b'#define XP_UNIX\n'+lines[-1])
env={**os.environ,'LD_LIBRARY_PATH':'/stage/usr/lib'}
version=subprocess.check_output(['/stage/usr/bin/js140','--version'],env=env,text=True).strip();assert '140.14' in version
r=subprocess.run(['/stage/usr/bin/js140','-e','print(6 * 7)'],env=env,capture_output=True,text=True,check=True);assert r.stdout.strip()=='42'
proof={'scope':'Native compile/install staging and actual JS shell arithmetic smoke only; original critical/API/JIT suites pending, no promotion or GNOME acceptance','version':version,'native_build_exit':0,'stage_exit':0,'staged_shell_exit':0,'arithmetic':'42','unqualified':'Critical original JS/API/JIT suites and dynamic consumer still required before owned promotion','static_archive_omitted':omitted,'js_config_original_sha256':hashlib.sha256(before).hexdigest(),'js_config_removed_lines':removed,'header_original_sha256':hashlib.sha256(before_header).hexdigest(),'header_fixed_sha256':hashlib.sha256(header.read_bytes()).hexdigest()}
Path('/build/stage-results.json').write_text(json.dumps(proof,indent=2)+'\n')
PY

#!/bin/bash
# Compiler-only phase; critical tests and native staging are separate gates.
set -euo pipefail
[[ $(id -u) == 101 && -d /src/rustc-1.97.1-src && -d /stage ]]
ulimit -c 0
python3 - <<'SPACE'
import os
s=os.statvfs('/build');assert s.f_bavail*s.f_frsize>=26*1024**3,'Preserve16GiB reserve plus10GiB compiler headroom'
SPACE
[[ $(llvm-config --version) == 22.1.8 ]]
mkdir /build/bootstrap
for component in rustc rust-std cargo; do
    sh "/src/bootstrap/$component-1.96.0-x86_64-unknown-linux-gnu/install.sh" \
        --destdir=/build/bootstrap --prefix=/usr --disable-ldconfig
done
python3 - <<'SEED'
import json,subprocess
from pathlib import Path
metadata=dict(line.split('=',1) for line in Path('/src/rustc-1.97.1-src/src/stage0').read_text().splitlines() if '=' in line and not line.startswith('#'))
root=Path('/build/bootstrap/usr');versions={}
for name in ['rustc','cargo','rustdoc']:
    text=subprocess.check_output([str(root/'bin'/name),'--version'],text=True).strip()
    assert text.startswith(name+' '+metadata['compiler_version']),text
    versions[name]=text
verbose=subprocess.check_output([str(root/'bin/rustc'),'--version','--verbose'],text=True)
assert 'commit-hash: '+metadata['compiler_git_commit_hash'] in verbose
assert Path(subprocess.check_output([str(root/'bin/rustc'),'--print','sysroot'],text=True).strip()).resolve()==root
Path('/build/bootstrap-proof.json').write_text(json.dumps({'scope':'Authenticated build-only seed in private work; not installed product compiler','versions':versions,'rustc_verbose':verbose,'source_manifest_commit':metadata['compiler_git_commit_hash']},indent=2)+'\n')
SEED
export PATH=/build/bootstrap/usr/bin:$PATH
export CARGO_HOME=/build/home/.cargo CARGO_NET_OFFLINE=true CARGO_BUILD_JOBS=4
export LIBSQLITE3_SYS_USE_PKG_CONFIG=1 OPENSSL_NO_VENDOR=1
# Frozen Rust source vendors this recommended dependency when absent, as the
# book permits. Never fetch a different libssh2 or update the foundation.
if pkg-config --exists libssh2; then export LIBSSH2_SYS_USE_PKG_CONFIG=1; fi
cd /src/rustc-1.97.1-src
python3 x.py --config /src/bootstrap.toml --build-dir /build/compile build
cd /build
python3 - <<'RESULT'
from pathlib import Path
import hashlib,json,os,subprocess
candidates={p.resolve() for p in Path('/build/compile').glob('*/stage2/bin/rustc') if p.is_file()}
assert len(candidates)==1,'Inspect actual stage2 layout; do not rebuild'
rustc=candidates.pop();assert rustc.is_relative_to('/build/compile')
verbose=subprocess.check_output([str(rustc),'--version','--verbose'],text=True)
assert verbose.startswith('rustc 1.97.1 ') and 'LLVM version: 22.1.8' in verbose
code=Path('/build/compiler-consumer.rs')
code.write_text('fn main() { let values=vec![1,2,3]; assert_eq!(values.iter().sum::<i32>(),6); assert_eq!(std::thread::spawn(|| 42).join().unwrap(),42); println!("toddy-native-rustc"); }\n')
subprocess.run([str(rustc),str(code),'-o','/build/compiler-consumer'],check=True)
assert subprocess.check_output(['/build/compiler-consumer'],text=True).strip()=='toddy-native-rustc'
s=os.statvfs('/build')
Path('/build/compile-result.json').write_text(json.dumps({'scope':'Native stage2 compilation and basic Vec/thread program only; critical tests/stage/install pending','version':'1.97.1','rustc_path':str(rustc),'rustc_verbose':verbose,'config_sha256':hashlib.sha256(Path('/src/bootstrap.toml').read_bytes()).hexdigest(),'compiler_consumer_exit':0,'free_bytes_after_compile':s.f_bavail*s.f_frsize},indent=2)+'\n')
RESULT

#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/h06/common.sh
cd /opt/toddy-build
python3 - <<'VERIFY'
from pathlib import Path
import json,sys,shutil
sys.path.insert(0,'scripts/build/phase2')
from verify_stage import inspect_stage
from package_copyright import write_copyright
assert Path('/var/log/toddy/phase2/llama-cpu-1.exit').read_text().strip()=='0'
source=Path('/mnt/lfs/sources/phase2/work/llama-cpu-1/stage')
before=inspect_stage(source)
assert 'usr/bin/llama-server' in before['entries']
assert 'usr/bin/llama-completion' in before['entries']
destination=Path('/mnt/lfs/sources/stage/phase2-llama-cpu')
assert not destination.exists(), 'Inspect existing stage before replay'
shutil.copytree(source,destination,symlinks=True)
assert inspect_stage(destination)==before
Path('/var/log/toddy/phase2/llama-cpu-stage.json').write_text(json.dumps(before,indent=2)+'\n')
write_copyright(destination,'llama-cpp',['llama.cpp-v0.9.0.tar.gz'])
profile={'schema_version':1,'cpu_flags':['sse4_2','avx','avx2','fma','f16c','bmi2'],
         'source_commit':'cd959bae99ff4bed22bef2604f45241c09bbb8c8',
         'gpu':False,'native_cpu_optimization':False,'subprocess_tools':False,
         'https_client':False,'weights_in_package':False}
(destination/'usr/share/doc/llama-cpp/cpu-profile.json').write_text(json.dumps(profile,indent=2)+'\n')
VERIFY
python3 scripts/build/stage_package.py llama-cpp 0.9.0-1+toddy1 \
    "$LFS/sources/stage/phase2-llama-cpu" --source llama.cpp-v0.9.0.tar.gz \
    --recipe scripts/build/phase2/llama-cpu-install.sh \
    --depends 'glibc (>= 2.44-1), gcc-runtime (>= 16.2.0-1)' --install

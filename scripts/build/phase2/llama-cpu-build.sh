#!/bin/bash
# Optional B03 CPU profile; no weights/downloaded UI/cloud/subprocess tools.
set -euo pipefail
[[ $(id -u) == 101 && -f /src/ggml/CMakeLists.txt && -d /stage ]]
python3 - <<'CPU'
from pathlib import Path
flags=set(next(l for l in Path('/proc/cpuinfo').read_text().splitlines() if l.startswith('flags')).split(':',1)[1].split())
assert {'sse4_2','avx','avx2','fma','f16c','bmi2'} <= flags, 'Selected optional AVX2 profile unavailable'
CPU
cmake -S /src -B /build/compile -G Ninja \
    -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=/usr \
    -DCMAKE_INSTALL_LIBDIR=lib -DCMAKE_SKIP_INSTALL_RPATH=ON \
    -DBUILD_SHARED_LIBS=ON -DLLAMA_BUILD_IS_DEV=OFF \
    -DLLAMA_BUILD_COMMON=ON -DLLAMA_BUILD_TOOLS=ON -DLLAMA_BUILD_SERVER=ON \
    -DLLAMA_BUILD_APP=OFF -DLLAMA_BUILD_EXAMPLES=OFF -DLLAMA_BUILD_TESTS=OFF \
    -DLLAMA_BUILD_UI=OFF -DLLAMA_USE_PREBUILT_UI=OFF -DLLAMA_CONNECT=OFF \
    -DLLAMA_OPENSSL=OFF -DLLAMA_SUBPROCESS=OFF -DLLAMA_LLGUIDANCE=OFF \
    -DGGML_NATIVE=OFF -DGGML_CPU=ON -DGGML_OPENMP=ON \
    -DGGML_SSE42=ON -DGGML_AVX=ON -DGGML_AVX2=ON -DGGML_BMI2=ON \
    -DGGML_FMA=ON -DGGML_F16C=ON -DGGML_AVX512=OFF \
    -DGGML_BLAS=OFF -DGGML_LLAMAFILE=OFF -DGGML_CUDA=OFF \
    -DGGML_VULKAN=OFF -DGGML_METAL=OFF -DGGML_RPC=OFF
cmake --build /build/compile --parallel 4 --target llama-server llama-completion
# Do not install unrelated tools/SDKs from the broad upstream default install.
# These targets build exactly their runtime shared-library dependencies in bin/.
python3 - <<'STAGE'
from pathlib import Path
import hashlib,json,shutil
source=Path('/build/compile/bin')
stage=Path('/stage/usr')
(stage/'bin').mkdir(parents=True)
(stage/'lib').mkdir()
for name in ['llama-server','llama-completion']:
    assert (source/name).is_file()
    shutil.copy2(source/name,stage/'bin'/name)
libraries=list(source.glob('*.so*'))
assert libraries
for path in libraries:
    assert path.resolve().is_relative_to(source) and path.is_file()
    shutil.copy2(path,stage/'lib'/path.name,follow_symlinks=False)
files={str(p.relative_to('/stage')):hashlib.sha256(p.read_bytes()).hexdigest()
       for p in stage.rglob('*') if p.is_file() and not p.is_symlink()}
Path('/build/selected-runtime.json').write_text(json.dumps(files,indent=2)+'\n')
STAGE
LD_LIBRARY_PATH=/stage/usr/lib /stage/usr/bin/llama-server --version
LD_LIBRARY_PATH=/stage/usr/lib /stage/usr/bin/llama-completion --version

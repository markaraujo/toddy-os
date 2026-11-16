#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile ]]
# Only the fixed CPU CLI target; internal GGML is statically linked, libc is not.
# Run in the qualified no-network, read-only /src build harness. No model/audio
# is a build dependency and no unqualified model inference is called a test pass.
cmake -S /src -B /build/compile -DCMAKE_INSTALL_PREFIX=/usr \
    -DCMAKE_INSTALL_LIBDIR=lib -DCMAKE_BUILD_TYPE=Release \
    -DFETCHCONTENT_FULLY_DISCONNECTED=ON -DBUILD_SHARED_LIBS=OFF \
    -DWHISPER_BUILD_IS_DEV=OFF -DWHISPER_BUILD_TESTS=OFF \
    -DWHISPER_BUILD_EXAMPLES=ON -DWHISPER_BUILD_SERVER=OFF \
    -DWHISPER_CURL=OFF -DWHISPER_SDL2=OFF -DWHISPER_COMMON_FFMPEG=OFF \
    -DGGML_NATIVE=OFF -DGGML_OPENMP=OFF -DGGML_CCACHE=OFF \
    -DGGML_CUDA=OFF -DGGML_VULKAN=OFF -DGGML_BLAS=OFF -DGGML_RPC=OFF \
    -DGGML_AVX=OFF -DGGML_AVX2=OFF -DGGML_FMA=OFF -DGGML_F16C=OFF -DGGML_BMI2=OFF \
    > /build/configure.log 2>&1
cmake --build /build/compile --target whisper-cli -j4 > /build/compile.log 2>&1
# Full cmake install would incorrectly require other, intentionally unbuilt tools.
install -Dm755 /build/compile/bin/whisper-cli /stage/usr/bin/whisper-cli
install -Dm644 /src/LICENSE /stage/usr/share/doc/whisper-cpp/LICENSE
install -Dm644 /src/ggml/LICENSE /stage/usr/share/doc/whisper-cpp/GGML-LICENSE
/stage/usr/bin/whisper-cli --help > /build/cli-help.log 2>&1
python3 - <<'CHECK'
from pathlib import Path
import json
Path('/build/test-results.json').write_text(json.dumps({
    'scope':'Native compile and CLI help only; actual multilingual inference is REQUIRED separately',
    'cli_help_exit':0,'model_inference_tested':False,'physical_audio_tested':False,
    'upstream_model_tests':'Not run: upstream matrix requires distinct tiny/base/etc test models; selected full multilingual base needs focused real EN/PT inference qualification.'},indent=2)+'\n')
CHECK

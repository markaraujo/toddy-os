#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && -d /stage ]]
export PIP_NO_INDEX=1 PYTHONDONTWRITEBYTECODE=1
python3 - <<'PY'
import shutil
shutil.copytree('/src','/build/source',symlinks=True)
PY
cd /build/source
pip3 wheel --no-index --no-cache-dir --no-build-isolation --no-deps --wheel-dir /build/wheels .
pip3 install --root=/stage --prefix=/usr --ignore-installed --no-index --no-deps --no-compile --find-links /build/wheels psutil==7.2.2
cd /build
PYTHONPATH=/stage/usr/lib/python3.14/site-packages python3 - < /src/toddy-probe.py > /build/consumer.json

#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/source ]]
export PIP_NO_INDEX=1 PIP_CONFIG_FILE=/dev/null PYTHONDONTWRITEBYTECODE=1 PYYAML_FORCE_LIBYAML=0
python3 - <<'PY'
import shutil
shutil.copytree('/src','/build/source',symlinks=True)
PY
cd /build/source
pip3 wheel --no-index --no-cache-dir --no-build-isolation --no-deps --wheel-dir /build/wheels .
pip3 install --root=/stage --prefix=/usr --ignore-installed --no-index --no-deps --no-compile --find-links /build/wheels PyYAML==6.0.3
cd /build
export PYTHONPATH=/stage/usr/lib/python3.14/site-packages
python3 /src/toddy-probe.py > /build/consumer.json
# test_all.py ignores its boolean result in __main__. Assert its real result,
# never infer suite acceptance from that entry point's unconditional exit0.
python3 - <<'PY' > /build/upstream-tests.log 2>&1
import sys
sys.path.insert(0,'/build/source/tests/legacy_tests')
import test_all
assert test_all.main([]), 'Upstream YAML fixture suite has failures/errors'
PY
python3 - <<'PY'
from pathlib import Path
import hashlib,json,re
path=Path('/build/upstream-tests.log');text=path.read_text()
match=re.search(r'^TESTS: (\d+)$',text,re.M);assert match and int(match[1])>1000
assert not re.search(r'^(FAILURES|ERRORS): [1-9]',text,re.M)
Path('/build/test-results.json').write_text(json.dumps({'pure_python_upstream_cases':int(match[1]),'upstream_boolean_result':True,'upstream_log_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'native_exit':0,'optional_libyaml_c_accelerator':'Not built; associated extension collection not registered','staged_consumer':json.loads(Path('/build/consumer.json').read_text())},indent=2)+'\n')
PY

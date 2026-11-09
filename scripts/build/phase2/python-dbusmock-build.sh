#!/bin/bash
# Test-only mock library; fixtures never establish real service acceptance.
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/source ]]
export PIP_NO_INDEX=1 PIP_CONFIG_FILE=/dev/null PIP_DISABLE_PIP_VERSION_CHECK=1
export PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1
cp -a /src /build/source
chmod -R u+w /build/source
cd /build/source
pip3 wheel --no-index --no-cache-dir --no-build-isolation --no-deps --wheel-dir /build/wheels . > /build/compile.log 2>&1
pip3 install --root=/stage --prefix=/usr --ignore-installed --no-index --no-deps --no-compile --find-links /build/wheels python-dbusmock==0.38.1 > /build/stage.log 2>&1
cd /build
export PYTHONPATH=/stage/usr/lib/python3.14/site-packages
# The published core API/CLI suite uses private buses. External clients/templates
# have their own service qualifications and are not claimed by this tooling gate.
python3 -m pytest -p no:cacheprovider /build/source/tests/test_api.py /build/source/tests/test_cli.py /build/source/tests/test_api_pytest.py::test_dbusmock_test --junitxml=/build/original-tests.xml > /build/original-tests.log 2>&1
python3 /src/toddy-probe.py > /build/native-consumer.json
python3 - <<'PY'
from pathlib import Path
import hashlib,json,xml.etree.ElementTree as ET
p=Path('/build');root=ET.parse(p/'original-tests.xml').getroot();cases=list(root.iter('testcase'));assert cases
assert not list(root.iter('failure')) and not list(root.iter('error'))
consumer=json.loads((p/'native-consumer.json').read_text())
proof={'scope':'Published core API/CLI programs and one pytest fixture test, private-bus mock typed RPC/error/recovery consumer; no real Polkit or device acceptance','compile_exit':0,'stage_exit':0,'original_cases':len(cases),'passed':sum(c.find('skipped') is None for c in cases),'skipped':[{'name':c.attrib['name'],'reason':c.find('skipped').attrib} for c in cases if c.find('skipped') is not None],'consumer':consumer,'stage_sha256':{str(f.relative_to(p/'stage')):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'stage').rglob('*') if f.is_file() and not f.is_symlink()}}
(p/'stage-results.json').write_text(json.dumps(proof,indent=2)+'\n')
PY

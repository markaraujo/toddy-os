#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/source ]]
export PIP_NO_INDEX=1 PIP_CONFIG_FILE=/dev/null PIP_DISABLE_PIP_VERSION_CHECK=1
export PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1
export PYTHONPATH=/src/toddy-backend/flit_core-3.12.0
python3 - <<'PY'
import flit_core,shutil
assert flit_core.__version__=='3.12.0'
shutil.copytree('/src','/build/source',symlinks=True)
PY
cd /build/source
pip3 wheel --no-index --no-cache-dir --no-build-isolation --no-deps --wheel-dir /build/wheels . > /build/compile.log 2>&1
pip3 install --root=/stage --prefix=/usr --ignore-installed --no-index --no-deps --no-compile --find-links /build/wheels docutils==0.23 > /build/stage.log 2>&1
cd /build
export PYTHONPATH=/stage/usr/lib/python3.14/site-packages
python3 -m unittest discover -s /build/source/test/test_writers -p test_manpage.py -v > /build/upstream-tests.log 2>&1
python3 /src/toddy-probe.py > /build/consumer.json 2>&1
printf 'toddy(1)\n========\n\nNAME\n----\n\nToddy offline.\n' | /stage/usr/bin/rst2man --syntax-highlight=none > /build/native-cli.man
python3 - <<'PY'
from pathlib import Path
import email.parser,hashlib,json,re,zipfile
w=Path('/build');files=list((w/'wheels').glob('*.whl'));assert len(files)==1
with zipfile.ZipFile(files[0]) as z:
    names=[n for n in z.namelist() if n.endswith('.dist-info/METADATA')];assert len(names)==1
    meta=email.parser.BytesParser().parsebytes(z.read(names[0]));assert meta['Name']=='docutils' and meta['Version']=='0.23'
text=(w/'upstream-tests.log').read_text();match=re.search(r'Ran ([0-9]+) tests?',text);assert match and '\nOK\n' in text and 'skipped=' not in text
assert b'Toddy offline.' in (w/'native-cli.man').read_bytes()
(w/'test-results.json').write_text(json.dumps({'scope':'Native original man writer cases, actual rst2man CLI and explicit include/raw-policy consumer; build tooling only, no desktop acceptance','upstream_manpage_cases':int(match.group(1)),'upstream_exit':0,'staged_consumer':json.loads((w/'consumer.json').read_text()),'staged_cli_exit':0,'private_backend':'Exact Flit3.12.0 per source >=3.11,<4; base4.0.2 unchanged','wheel_sha256':hashlib.sha256(files[0].read_bytes()).hexdigest()},indent=2)+'\n')
PY

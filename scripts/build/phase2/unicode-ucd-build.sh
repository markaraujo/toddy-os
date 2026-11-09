#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /stage/usr ]]
mkdir -p /stage/usr/share/unicode
cp -R /src/ucd /stage/usr/share/unicode/ucd
chmod -R u+w /stage/usr/share/unicode/ucd
python3 /src/toddy-probe.py /stage > /build/native-consumer.json
python3 - <<'PY'
from pathlib import Path
import hashlib,json
p=Path('/build');source=Path('/src/ucd');stage=Path('/stage/usr/share/unicode/ucd')
def manifest(base):return {str(f.relative_to(base)):hashlib.sha256(f.read_bytes()).hexdigest() for f in base.rglob('*') if f.is_file()}
assert manifest(source)==manifest(stage)
r={'scope':'Actual UCD17data/version/Unicode scalar/field/range/Portuguese/emoji metadata and exact staged bytes only; no glyph/input/native GNOME acceptance','stage_exit':0,'original_suite':'Upstream static data has no registered executable suite; explicit actual data invariants checked','consumer':json.loads((p/'native-consumer.json').read_text()),'source_manifest':manifest(source),'stage_sha256':{str(f.relative_to(p/'stage')):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'stage').rglob('*') if f.is_file() and not f.is_symlink()}}
(p/'stage-results.json').write_text(json.dumps(r,indent=2)+'\n')
PY

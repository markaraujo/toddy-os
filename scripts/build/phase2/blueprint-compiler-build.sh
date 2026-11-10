#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile ]]
export PYTHONDONTWRITEBYTECODE=1 GSETTINGS_BACKEND=memory
meson setup /build/compile /src --prefix=/usr --libdir=lib --buildtype=release --wrap-mode=nofallback -Ddocs=false -Dpython.bytecompile=-1
ninja -C /build/compile -j2
# Pure tokenizer/formatter/linter programs only. Book full suite needs a display;
# sample Gtk.Builder/deprecation branches remain deferred, not passes.
mkdir /build/private-tests
cp -a /src/tests /build/private-tests/tests
(cd /build/private-tests; PYTHONPATH=/src python3 -B -m unittest -v tests.test_tokenizer tests.test_formatter tests.test_linter) > /build/original-selected-tests.log 2>&1
printf '0\n' > /build/original-selected-tests.exit
meson install -C /build/compile --no-rebuild --destdir /stage
export PYTHONPATH=/stage/usr/lib/python3.14/site-packages
python3 /src/toddy-probe.py /stage/usr/bin/blueprint-compiler > /build/native-consumer.json
python3 - <<'PY'
from pathlib import Path
import hashlib,json,re
w=Path('/build');log=(w/'original-selected-tests.log').read_text();count=re.findall(r'^Ran (\d+) tests? in ',log,re.M);assert len(count)==1 and re.search(r'^OK$',log,re.M) and not re.search(r'\b(?:skipped|FAILED|ERROR)\b',log)
r={'scope':'Frozen blueprint compiler0.22.2 build-only SDK; original tokenizer/formatter/linter selected programs and own CLI XML/refusal/recovery. Full GTK Builder/deprecation display suite unexecuted; no widget/GNOME acceptance.','compile_exit':0,'stage_exit':0,'original_selected_test_cases':int(count[0]),'original_selected_test_modules':['tests.test_tokenizer','tests.test_formatter','tests.test_linter'],'deferred':['tests.test_samples','tests.test_deprecations'],'consumer':json.loads((w/'native-consumer.json').read_text()),'stage_sha256':{str(p.relative_to('/stage')):hashlib.sha256(p.read_bytes()).hexdigest() for p in Path('/stage').rglob('*') if p.is_file() and not p.is_symlink()}}
(w/'stage-results.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k!='stage_sha256'}))
PY

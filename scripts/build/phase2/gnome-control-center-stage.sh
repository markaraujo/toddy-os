#!/bin/bash
set -euo pipefail
test "$(id -u)" = 101
test -s /build/portable-tests-results.json
test -z "$(find /stage -mindepth 1 -print -quit)"
export PYTHONDONTWRITEBYTECODE=1 GTK_A11Y=none
meson install -C /build/compile --no-rebuild --destdir=/stage > /build/original-stage.log 2>&1
test -x /stage/usr/bin/gnome-control-center
/stage/usr/bin/gnome-control-center --version > /build/local-version.log
XDG_CURRENT_DESKTOP=GNOME /stage/usr/bin/gnome-control-center --list > /build/local-panels.log
set +e
/stage/usr/bin/gnome-control-center --toddy-invalid-option > /build/local-refusal.log 2>&1
refused=$?
set -e
test "$refused" -ne 0
XDG_CURRENT_DESKTOP=GNOME /stage/usr/bin/gnome-control-center --list > /build/local-panels-recovered.log
cmp /build/local-panels.log /build/local-panels-recovered.log
ldd /stage/usr/bin/gnome-control-center > /build/local-linkage.log
python3 - "$refused" <<'PYTEST'
from pathlib import Path
import hashlib
import json
import os
import sys
work=Path('/build')
stage=Path('/stage')
assert (work/'local-version.log').read_text().strip() == 'Local options gnome-control-center 50.4'
text=(work/'local-panels.log').read_text()
for panel in ('network','printers','system','display','sound','keyboard'):
    assert panel in text,panel
assert 'not found' not in (work/'local-linkage.log').read_text()
original=json.loads((work/'compile-results.json').read_text())
for relative,sha in original['artifacts'].items():
    with (work/'compile'/relative).open('rb') as stream:assert hashlib.file_digest(stream,'sha256').hexdigest()==sha
payload={str(path.relative_to(stage)):hashlib.sha256(path.read_bytes()).hexdigest()
         for path in stage.rglob('*') if path.is_file() and not path.is_symlink()}
assert 'usr/bin/gnome-control-center' in payload
assert os.statvfs(work).f_bavail*os.statvfs(work).f_frsize >= 128*1024**2
(work/'stage-results.json').write_text(json.dumps({'version':'50.4','stage_exit':0,'stage_sha256':payload,
    'unchanged_elf_count':len(original['artifacts']),'invalid_option_exit':int(sys.argv[1]),
    'scope':'Private staged CLI version and compiled panel metadata, invalid-option refusal and recovery. No graphical window or panel actions tested.'},indent=2)+'\n')
PYTEST

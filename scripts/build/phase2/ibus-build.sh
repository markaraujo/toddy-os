#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/source ]]
export PYTHONDONTWRITEBYTECODE=1
cp -a /src /build/source
chmod -R u+w /build/source
cd /build/source
# Frozen BLFS corrections, restricted to this private working copy.
python3 - <<'PY'
from pathlib import Path
import hashlib,json
changes=[]
for name in ['data/dconf/org.freedesktop.ibus.gschema.xml','Makefile.am','configure.ac','engine/test-gnome.py','client/gtk2/ibusimcontext.c']:
 p=Path(name);before=p.read_bytes()
 if name.endswith('ibusimcontext.c'):
  old=b'#ifdef HAVE_XIM\n    display = gtk_widget_get_display (ibusimcontext->client_window);\n'
  assert before.count(old)==1
  after=before.replace(old,b'    display = gtk_widget_get_display (ibusimcontext->client_window);\n#if defined(HAVE_XIM) && defined(GDK_WINDOWING_X11)\n')
 elif name.endswith('.xml'):
  assert b'/desktop/ibus' in before;after=before.replace(b'/desktop/ibus',b'/org/freedesktop/ibus')
 elif name in ['Makefile.am','configure.ac']:
  after=b''.join(line for line in before.splitlines(keepends=True) if b'docs' not in line and b'GTK_DOC' not in line)
 else:
  after=before.replace(b'#!/usr/bin/env python\n',b'#!/usr/bin/env python3\n')
 if after!=before:
  p.write_bytes(after);changes.append({'path':name,'before_sha256':hashlib.sha256(before).hexdigest(),'after_sha256':hashlib.sha256(after).hexdigest()})
Path('/build/source-corrections.json').write_text(json.dumps(changes,indent=2)+'\n')
PY
SAVE_DIST_FILES=1 NOCONFIGURE=1 ./autogen.sh > /build/autogen.log 2>&1
CFLAGS='-O2 -std=gnu17' ./configure --prefix=/usr --sysconfdir=/etc --libdir=/usr/lib \
 --disable-xim --disable-static --disable-python2 --disable-appindicator --disable-gtk2 \
 --disable-emoji-dict --enable-gtk4 --enable-wayland --enable-introspection \
 --enable-memconf --disable-schemas-install > /build/configure.log 2>&1
make -j4 'test_stress_LDADD=$(AM_LDADD) -lX11' > /build/compile.log 2>&1
# Portable originals only. Display/private bus/uinput/locale-sensitive programs
# remain unexecuted until their native runtime gate, never reported as passes.
make -C src/tests -j4 check TESTS='ibus-keynames ibus-registry ibus-serializable ibus-share ibus-util ibus-keyval' > /build/original-tests.log 2>&1
make -C bus check TESTS='test-matchrule' >> /build/original-tests.log 2>&1
make DESTDIR=/stage install > /build/stage.log 2>&1
cc /src/toddy-probe.c -I/stage/usr/include/ibus-1.0 -L/stage/usr/lib \
 $(pkg-config --cflags --libs gio-2.0) -libus-1.0 -Wl,-rpath,/stage/usr/lib -o /build/native-probe
LD_LIBRARY_PATH=/stage/usr/lib /build/native-probe > /build/native-consumer.json
python3 - <<'PY'
from pathlib import Path
import hashlib,json,re
p=Path('/build');tests=[]
for folder in ['src/tests','bus']:
 for f in (p/'source'/folder).glob('*.trs'):
  m=re.search(r'^:test-result: (\S+)$',f.read_text(),re.M);assert m and m[1]=='PASS'
  tests.append({'name':str(f.relative_to(p/'source')),'result':m[1]})
assert len(tests)==7
result={'scope':'Seven selected portable original drivers and actual UTF8 serialization/key parser refusal/recovery. Private-bus/display/uinput/locale-sensitive originals and GNOME/real keyboard remain pending.', 'compile_exit':0,'stage_exit':0,'original_tests':tests,'consumer':json.loads((p/'native-consumer.json').read_text()),'source_corrections':json.loads((p/'source-corrections.json').read_text()),'artifacts':{str(f.relative_to(p/'source')):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'source').rglob('*') if f.is_file() and not f.is_symlink() and f.open('rb').read(4)==b'\x7fELF'},'stage_sha256':{str(f.relative_to(p/'stage')):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'stage').rglob('*') if f.is_file() and not f.is_symlink()}}
(p/'stage-results.json').write_text(json.dumps(result,indent=2)+'\n')
PY

#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile ]]
export PYTHONDONTWRITEBYTECODE=1
ulimit -c 0
[[ $(pkg-config --modversion libarchive) == 3.8.11 ]]
meson setup /build/compile /src --prefix=/usr --libdir=lib --buildtype=release \
 --wrap-mode=nofallback -Dgtk=true -Dintrospection=enabled -Dvapi=true -Dtests=true -Dgtk_doc=false
ninja -C /build/compile -j4
meson introspect /build/compile --tests > /build/original-registered-tests.json
python3 - <<'PY'
from pathlib import Path
import hashlib,json,os,shutil,subprocess
w=Path('/build');source=Path('/src/tests/files/extract');private=w/'test-fixtures/tests/files/extract'
def manifest(base):
 result={}
 for p in base.rglob('*'):
  rel=str(p.relative_to(base));row={'mode':p.lstat().st_mode}
  if p.is_symlink():row['symlink']=os.readlink(p)
  elif p.is_file():row['sha256']=hashlib.sha256(p.read_bytes()).hexdigest()
  else:row['directory']=True
  result[rel]=row
 return result
before=manifest(source);assert before and not private.exists();shutil.copytree(source,private,symlinks=True);assert manifest(private)==before
(w/'original-fixtures-manifest.json').write_text(json.dumps({'scope':'Byte/mode/link identical private original fixture copy; only output subdirectories writable test products, source remains RO','entries':[{'path':n,**v} for n,v in sorted(before.items())]},indent=2)+'\n')
rows=json.loads((w/'original-registered-tests.json').read_text());assert len(rows)==1 and rows[0]['name']=='test-extract-unit'
env=dict(os.environ,G_TEST_SRCDIR='/build/test-fixtures');command=['/build/compile/tests/test-extract-unit','--tap']
with (w/'original-tests.log').open('xb') as out:r=subprocess.run(command,env=env,stdout=out,stderr=subprocess.STDOUT)
(w/'original-tests.exit').write_text(str(r.returncode)+'\n');assert r.returncode==0
assert manifest(source)==before
after=manifest(private)
for name,value in before.items():
 if 'output' not in Path(name).parts:assert after.get(name)==value
assert not Path('/tmp/arextract.txt').exists()
(w/'original-fixtures-verified.json').write_text(json.dumps({'source_unchanged':True,'private_input_reference_unchanged':True,'original_binary_unmodified':True,'tmp_symlink_escape_not_created':True,'fixture_entries':len(before),'manifest_sha256':hashlib.sha256((w/'original-fixtures-manifest.json').read_bytes()).hexdigest()},indent=2)+'\n')
PY
meson install -C /build/compile --destdir /stage --no-rebuild
cc /src/toddy-probe.c -I/stage/usr/include/gnome-autoar-0 -L/stage/usr/lib \
 $(pkg-config --cflags --libs gio-2.0) -lgnome-autoar-0 -Wl,-rpath,/stage/usr/lib -o /build/native-probe
python3 - <<'PY'
from pathlib import Path
import zipfile,hashlib,json
p=Path('/build/consumer');p.mkdir()
with zipfile.ZipFile(p/'payload.zip','w',compression=zipfile.ZIP_DEFLATED) as z:z.writestr('documento-ã.txt','Olá Toddy\n')
(p/'empty.zip').write_bytes(b'');(p/'source-hashes.json').write_text(json.dumps({n:hashlib.sha256((p/n).read_bytes()).hexdigest() for n in ['payload.zip','empty.zip']},indent=2)+'\n')
PY
/build/native-probe /build/consumer > /build/native-consumer.json
GI_TYPELIB_PATH=/stage/usr/lib/girepository-1.0 LD_LIBRARY_PATH=/stage/usr/lib python3 - <<'PY' > /build/GI-consumer.json
import gi,json
gi.require_version('GnomeAutoar','0.1');gi.require_version('GnomeAutoarGtk','0.1')
from gi.repository import GnomeAutoar,GnomeAutoarGtk
assert GnomeAutoar.Extractor.__gtype__.name=='AutoarExtractor'
print(json.dumps({'namespace':'GnomeAutoar0.1/GnomeAutoarGtk0.1','GI_type':'AutoarExtractor','widget_tested':False}))
PY
python3 - <<'PY'
from pathlib import Path
import hashlib,json,re
p=Path('/build');text=(p/'original-tests.log').read_text();cases=re.findall(r'^ok\s+\d+[^\n]*',text,re.M);assert cases and not re.search(r'^not ok',text,re.M)
for n,sha in json.loads((p/'consumer/source-hashes.json').read_text()).items():assert hashlib.sha256((p/'consumer'/n).read_bytes()).hexdigest()==sha
r={'scope':'Frozen gnome-autoar0.4.5 core/GTK3/GI/Vala, existing owned libarchive3.8.11 reused per ADR0017 (no book downgrade). Original registered extraction unit binary runs against identical private fixture copy because upstream writes output under fixture directories; source/input/reference unchanged. Manual create/extract/UI programs compile only. Actual ZIP UTF8/empty refusal/precancel no-effect/recovery/source retention C and GI userspace, no GUI/mid-extraction Stop acceptance.','compile_exit':0,'stage_exit':0,'original_registered_programs':1,'original_unit_cases':cases,'original_fixture_verification':json.loads((p/'original-fixtures-verified.json').read_text()),'reused_libarchive_version':'3.8.11','consumer':json.loads((p/'native-consumer.json').read_text()),'GI_consumer':json.loads((p/'GI-consumer.json').read_text()),'artifacts':{str(f.relative_to(p/'compile')):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'compile').rglob('*') if f.is_file() and not f.is_symlink() and f.open('rb').read(4)==b'\x7fELF'},'stage_sha256':{str(f.relative_to(p/'stage')):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'stage').rglob('*') if f.is_file() and not f.is_symlink()}}
(p/'stage-results.json').write_text(json.dumps(r,indent=2)+'\n')
PY

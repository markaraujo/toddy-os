#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile ]]
export PYTHONDONTWRITEBYTECODE=1 LC_ALL=C
ulimit -c 0
mkdir /build/compile
cd /build/compile
/src/configure --prefix=/usr --libdir=/usr/lib --disable-static --without-python --with-default-dict=/usr/lib/cracklib/pw_dict > /build/original-configure.log 2>&1
make -j4 > /build/original-build.log 2>&1
make check > /build/original-tests.log 2>&1
make DESTDIR=/stage install > /build/original-install.log 2>&1
python3 - <<'PY'
from pathlib import Path
import hashlib,json,lzma,os
row=json.loads(Path('/src/toddy-prepared.json').read_text())['extra_source'];compressed=Path('/src/toddy-words.xz');assert hashlib.sha256(compressed.read_bytes()).hexdigest()==row['sha256']
s=os.statvfs('/build');assert s.f_bavail*s.f_frsize>=16*1024**3+48*1024**2
h=hashlib.sha256();size=lines=0
with lzma.open(compressed,'rb') as stream,Path('/build/original-words').open('xb') as out:
 while block:=stream.read(1024*1024):
  size+=len(block);assert size<=row['expanded_bytes'];lines+=block.count(b'\n');h.update(block);out.write(block)
assert size==row['expanded_bytes'] and lines==row['lines'] and h.hexdigest()==row['expanded_sha256']
PY
mkdir -p /stage/usr/lib/cracklib
# Keep raw dictionary in the reproducible build inputs; only packed runtime indices
# are installed. Use a fixed product word instead of the builder's host name.
printf 'toddy\n' > /build/product-extra-words
/src/util/cracklib-format /build/original-words /build/product-extra-words | /build/compile/util/cracklib-packer /stage/usr/lib/cracklib/pw_dict > /build/dictionary-pack.log 2>&1
python3 - <<'PY'
from pathlib import Path
import hashlib,json,os
w=Path('/build');logs=list((w/'compile').rglob('test-suite.log'));assert len(logs)==1
log=logs[0].read_text();assert '# TOTAL: 2' in log and '# PASS:  2' in log and '# FAIL:  0' in log
for suffix in ['hwm','pwd','pwi']:assert (Path('/stage/usr/lib/cracklib')/('pw_dict.'+suffix)).is_file()
r={'scope':'Cracklib2.10.3 LGPL2.1 shared library/tools and exact recommended wordlist packed indices; two original endian/dictionary programs passed. Raw wordlist retained as build source, not installed duplicate; fixed product word avoids builder identity. Optional Python unselected. No PAM/account/system-password mutation, no full multilingual password security claim.','compile_exit':0,'stage_exit':0,'original_test_suite':log,'dictionary_source':json.loads(Path('/src/toddy-prepared.json').read_text())['extra_source'],'artifacts':{str(p.relative_to(w/'compile')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (w/'compile').rglob('*') if p.is_file() and not p.is_symlink() and p.open('rb').read(4)==b'\x7fELF'},'stage_sha256':{str(p.relative_to('/stage')):hashlib.sha256(p.read_bytes()).hexdigest() for p in Path('/stage').rglob('*') if p.is_file() and not p.is_symlink()}}
(w/'stage-results.json').write_text(json.dumps(r,indent=2)+'\n');s=os.statvfs('/build');assert s.f_bavail*s.f_frsize>=16*1024**3
PY

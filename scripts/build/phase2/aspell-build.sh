#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile && -x /usr/bin/which ]]
export PYTHONDONTWRITEBYTECODE=1
ulimit -c 0
mkdir /build/compile
cd /build/compile
# GNU Aspell has no original suite (frozen BLFS13.1). Keep optimized production
# without debug symbols; own real C API/CLI qualification follows dictionary build.
CFLAGS=-O2 CXXFLAGS=-O2 /src/configure --prefix=/usr --libdir=/usr/lib
python3 - <<'PY'
from pathlib import Path
import json,os,signal,subprocess,time
floor=16*1024**3;margin=16*1024**2
s=os.statvfs('/build');initial=s.f_bavail*s.f_frsize;assert initial>floor+margin
p=subprocess.Popen(['make','-j4'],start_new_session=True);minimum=initial;interrupted=False
while p.poll() is None:
 s=os.statvfs('/build');free=s.f_bavail*s.f_frsize;minimum=min(minimum,free)
 if free<floor+margin and not interrupted:os.killpg(p.pid,signal.SIGINT);interrupted=True
 time.sleep(0.25)
s=os.statvfs('/build');final=s.f_bavail*s.f_frsize;minimum=min(minimum,final)
Path('/build/compile-resource.json').write_text(json.dumps({'exit':p.returncode,'initial_free':initial,'minimum_free':minimum,'final_free':final,'reserve':floor,'stop_margin':margin,'interrupted':interrupted},indent=2)+'\n')
assert p.returncode==0 and not interrupted and minimum>=floor
PY
make DESTDIR=/stage install
# Global Info index is generated shared state, not an Aspell-owned payload.
mv /stage/usr/share/info/dir /build/aspell-generated-info-dir
ln -s aspell-0.60 /stage/usr/lib/aspell
python3 - <<'PY'
from pathlib import Path
import hashlib,json,shutil
src=Path('/src/toddy-dictionary-source');dest=Path('/build/dictionary-source');assert not dest.exists()
def manifest(base):return {str(p.relative_to(base)):hashlib.sha256(p.read_bytes()).hexdigest() for p in base.rglob('*') if p.is_file() and not p.is_symlink()}
before=manifest(src);shutil.copytree(src,dest,symlinks=True);assert before==manifest(dest)==manifest(src)
Path('/build/dictionary-source-before.json').write_text(json.dumps(before,sort_keys=True)+'\n')
PY
mkdir /build/private-bin
cat > /build/private-bin/aspell <<'WRAPPER'
#!/bin/bash
exec /build/compile/aspell --data-dir=/stage/usr/lib/aspell-0.60 --dict-dir=/build/dictionary-source "$@"
WRAPPER
chmod 755 /build/private-bin/aspell
cp /src/toddy-dictionary-source/{en.dat,en_phonet.dat,en_affix.dat} /stage/usr/lib/aspell-0.60/
cd /build/dictionary-source
ASPELL=/build/private-bin/aspell PREZIP=/build/compile/prezip-bin ./configure
make -j2
make DESTDIR=/stage dictdir=/usr/lib/aspell-0.60 datadir=/usr/lib/aspell-0.60 install
mkdir -p /stage/usr/share/doc/aspell/dictionary-en
cp /src/toddy-dictionary-source/{Copyright,README,README.iso} /stage/usr/share/doc/aspell/dictionary-en/
LD_LIBRARY_PATH=/stage/usr/lib python3 /src/toddy-probe.py /stage /build/consumer > /build/native-consumer.json
python3 - <<'PY'
from pathlib import Path
import hashlib,json,os
w=Path('/build');consumer=json.loads((w/'native-consumer.json').read_text());assert consumer['recovery_cycles']==2 and consumer['CLI_pipe_and_unknown_option']
original=json.loads((w/'dictionary-source-before.json').read_text());assert original=={str(p.relative_to('/src/toddy-dictionary-source')):hashlib.sha256(p.read_bytes()).hexdigest() for p in Path('/src/toddy-dictionary-source').rglob('*') if p.is_file() and not p.is_symlink()}
s=os.statvfs('/build');assert s.f_bavail*s.f_frsize>=16*1024**3
r={'scope':'Frozen Aspell0.60.8.2 optimized shared C/C++ API/CLI with real official English SCOWL2020.12.07 dictionary. Upstream package has no original test suite per frozen book. Own actual C API/CLI known/misspelling/suggestion/UTF8 personal persistence/session clear/malformed dictionary+invalid language/option refusal/input retention/recovery. No Portuguese lexicon, Enchant, Libspelling, editor, GUI or general parser-security acceptance. Readonly source and byte-identical private dictionary build copy, owned Which reused.','compile_exit':0,'stage_exit':0,'original_tests':'No upstream test suite; not reported as a passing original suite.','consumer':consumer,'resource':json.loads((w/'compile-resource.json').read_text()),'artifacts':{str(p.relative_to(w/'compile')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (w/'compile').rglob('*') if p.is_file() and not p.is_symlink() and p.open('rb').read(4)==b'\x7fELF'},'stage_sha256':{str(p.relative_to('/stage')):hashlib.sha256(p.read_bytes()).hexdigest() for p in Path('/stage').rglob('*') if p.is_file() and not p.is_symlink()}}
(w/'stage-results.json').write_text(json.dumps(r,indent=2)+'\n')
PY

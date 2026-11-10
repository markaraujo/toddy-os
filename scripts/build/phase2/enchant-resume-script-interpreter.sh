#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 ]]
export PYTHONDONTWRITEBYTECODE=1 PKG_CONFIG_PATH=/build/test-sdk/lib/pkgconfig
ulimit -c 0
[[ $(pkg-config --modversion 'UnitTest++') == 2.0.0 ]]
python3 - <<'PRE'
from pathlib import Path
import hashlib,json
w=Path('/build');assert (w/'compile').is_dir() and not list((w/'compile').iterdir())
assert json.loads((w/'sdk-resume-2-before.json').read_text())=={str(p.relative_to(w)):hashlib.sha256(p.read_bytes()).hexdigest() for base in ['sdk-compile','test-sdk'] for p in (w/base).rglob('*') if p.is_file() and not p.is_symlink() and (p.open('rb').read(4)==b'\x7fELF' or p.suffix=='.a')}
assert Path('/src/configure').stat().st_mode&0o777==0o754
PRE
guarded() {
 python3 - "$@" <<'PY'
from pathlib import Path
import json,os,signal,subprocess,sys,time
phase=sys.argv[1];out=Path('/build/resource-'+phase+'.json');assert not out.exists()
floor=16*1024**3;margin=16*1024**2;s=os.statvfs('/build');initial=s.f_bavail*s.f_frsize;assert initial>floor+margin
p=subprocess.Popen(sys.argv[2:],start_new_session=True);minimum=initial;interrupted=False
while p.poll() is None:
 s=os.statvfs('/build');free=s.f_bavail*s.f_frsize;minimum=min(minimum,free)
 if free<floor+margin and not interrupted:os.killpg(p.pid,signal.SIGINT);interrupted=True
 time.sleep(0.25)
s=os.statvfs('/build');final=s.f_bavail*s.f_frsize;minimum=min(minimum,final)
out.write_text(json.dumps({'exit':p.returncode,'initial_free':initial,'minimum_free':minimum,'final_free':final,'reserve':floor,'stop_margin':margin,'interrupted':interrupted},indent=2)+'\n')
assert p.returncode==0 and not interrupted and minimum>=floor
PY
}
cd /build/compile
CONFIG_SHELL=/bin/bash CFLAGS=-O2 CXXFLAGS=-O2 /bin/bash /src/configure --prefix=/usr --libdir=/usr/lib --sysconfdir=/etc --disable-static --enable-relocatable --with-aspell --without-hunspell --without-nuspell --without-hspell --without-voikko --without-zemberek
[[ $(grep -c '^UNITTESTPP_LIBS =.*UnitTest' Makefile) == 1 ]]
guarded main make -j4 > /build/original-build.log 2>&1
# /usr plus /etc makes upstream CLI scripts exit0 before executing; record those
# four scripts as unexecuted, not passing. Run both full original API drivers.
guarded tests make -C tests check -j2 "LOG_COMPILER=/bin/bash /src/tests/run-test" > /build/original-tests.log 2>&1
make DESTDIR=/stage install
LD_LIBRARY_PATH=/stage/usr/lib python3 /src/toddy-probe.py /stage /build/consumer > /build/native-consumer.json
python3 - <<'PY'
from pathlib import Path
import hashlib,json,re
w=Path('/build');log=(w/'sdk-original-build-tests.log').read_text();sdk=re.findall(r'Success: (\d+) tests passed\.',log);assert len(sdk)==1 and int(sdk[0])>0
rows=[]
for name in ['main','providers']:
 log=(w/'compile/tests'/(name+'.log')).read_text();counts=re.findall(r'Success: (\d+) tests passed\.',log);assert len(counts)==1 and int(counts[0])>0
 trs=(w/'compile/tests'/(name+'.trs')).read_text();assert ':test-result: PASS' in trs
 rows.append({'name':name,'exit':0,'cases':int(counts[0])})
r={'scope':'Frozen Enchant2.8.19 Aspell-only real provider, supported relocatable build required by original tests; no optional provider breadth. Private UnitTest++2.0.0 PIC static SDK and its complete original tests, both original Enchant API/provider programs. Four upstream CLI programs unexecuted because /usr prefix plus /etc sysconfdir causes their harness to exit0; not passes. Own real Aspell English/UTF8 personal persistence/session/refusal/recovery/CLI. No editor/GUI/Portuguese lexicon/general parser-security qualification.','compile_exit':0,'stage_exit':0,'private_sdk_original_cases':int(sdk[0]),'private_sdk_installed_to_system':False,'original_tests':rows,'original_program_scripts_not_executed':['misspelled-input.sh','unknown-option.sh','zero-arguments.sh','run-enchant-lsmod.sh'],'consumer':json.loads((w/'native-consumer.json').read_text()),'resources':{name:json.loads((w/('resource-'+name+'.json')).read_text()) for name in ['sdk','main','tests']},'artifacts':{str(p.relative_to(w/'compile')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (w/'compile').rglob('*') if p.is_file() and not p.is_symlink() and p.open('rb').read(4)==b'\x7fELF'},'stage_sha256':{str(p.relative_to('/stage')):hashlib.sha256(p.read_bytes()).hexdigest() for p in Path('/stage').rglob('*') if p.is_file() and not p.is_symlink()}}
(w/'stage-results.json').write_text(json.dumps(r,indent=2)+'\n')
PY

python3 - <<'POST'
from pathlib import Path
import hashlib,json
w=Path('/build');assert json.loads((w/'sdk-resume-2-before.json').read_text())=={str(p.relative_to(w)):hashlib.sha256(p.read_bytes()).hexdigest() for base in ['sdk-compile','test-sdk'] for p in (w/base).rglob('*') if p.is_file() and not p.is_symlink() and (p.open('rb').read(4)==b'\x7fELF' or p.suffix=='.a')}
POST

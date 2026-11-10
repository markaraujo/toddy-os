#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile && ! -e /build/sdk-compile ]]
export PYTHONDONTWRITEBYTECODE=1
ulimit -c 0
# Bound each compiler phase; this never interrupts a native package transaction.
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
# CMake4.4 documents the external minimum-policy knob for unchanged old projects.
# Assertions remain enabled in the private, PIC static test SDK. Never installed.
cmake -S /src/toddy-test-sdk -B /build/sdk-compile -G Ninja -DCMAKE_INSTALL_PREFIX=/build/test-sdk -DPACKAGE_VERSION=2.0.0 -DCMAKE_POLICY_VERSION_MINIMUM=3.5 -DCMAKE_BUILD_TYPE=Debug -DCMAKE_CXX_FLAGS_DEBUG=-O2 -DCMAKE_POSITION_INDEPENDENT_CODE=ON -DUTPP_AMPLIFY_WARNINGS=OFF -DUTPP_INCLUDE_TESTS_IN_BUILD=ON
# Upstream post-build step runs its own complete test runner exactly once.
guarded sdk cmake --build /build/sdk-compile -j4 > /build/sdk-original-build-tests.log 2>&1
cmake --install /build/sdk-compile
install -m644 /src/toddy-test-sdk/LICENSE /build/test-sdk/LICENSE
# Private-prefix consumers use both UnitTest++.h and UnitTest++/UnitTest++.h.
python3 - <<'SDKPC'
from pathlib import Path
p=Path('/build/test-sdk/lib/pkgconfig/UnitTest++.pc');s=p.read_text();assert s.count('Cflags: -I${includedir}/')==1
p.write_text(s.replace('Cflags: -I${includedir}/','Cflags: -I${includedir}/ -I${includedir}/..'))
SDKPC
export PKG_CONFIG_PATH=/build/test-sdk/lib/pkgconfig
[[ $(pkg-config --modversion 'UnitTest++') == 2.0.0 ]]
mkdir /build/compile
cd /build/compile
CONFIG_SHELL=/bin/bash CFLAGS=-O2 CXXFLAGS=-O2 /bin/bash /src/configure --prefix=/usr --libdir=/usr/lib --sysconfdir=/etc --disable-static --enable-relocatable --with-aspell --without-hunspell --without-nuspell --without-hspell --without-voikko --without-zemberek
[[ $(grep -c '^UNITTESTPP_LIBS =.*UnitTest' Makefile) == 1 ]]
guarded main make -j4 > /build/original-build.log 2>&1
# /usr plus /etc makes upstream CLI scripts exit0 before executing; record those
# four scripts as unexecuted, not passing. Run both full original API drivers.
guarded tests make -C tests check -j2 "LOG_COMPILER=/bin/bash /src/tests/run-test" "UNITTESTPP_CFLAGS=$(pkg-config --cflags UnitTest++)" > /build/original-tests.log 2>&1
make DESTDIR=/stage install
mkdir -p /build/provider-direct/config
set +e
(cd /build/compile/tests && ENCHANT_CONFIG_DIR=/build/provider-direct/config LD_LIBRARY_PATH=/stage/usr/lib LIBTOOL=/build/compile/libtool /bin/bash /src/tests/run-test ./providers.test /stage/usr/lib/enchant-2/enchant_aspell.so) > /build/original-provider-explicit.log 2>&1
provider_exit=$?
set -e
printf '%s\n' "$provider_exit" > /build/original-provider-explicit.exit
[[ $provider_exit == 0 ]]
LD_LIBRARY_PATH=/stage/usr/lib python3 /src/toddy-probe.py /stage /build/consumer > /build/native-consumer.json
python3 - <<'PY'
from pathlib import Path
import hashlib,json,re
w=Path('/build');log=(w/'sdk-original-build-tests.log').read_text();sdk=re.findall(r'Success: ([0-9]+) tests passed[.]',log);assert len(sdk)==1 and int(sdk[0])>0
rows=[]
for name in ['main','providers']:
 log=(w/'compile/tests'/(name+'.log')).read_text();counts=re.findall(r'Success: ([0-9]+) tests passed[.]',log)
 trs=(w/'compile/tests'/(name+'.trs')).read_text();assert ':test-result: PASS' in trs
 if name=='main':assert counts==['432']
 rows.append({'name':name,'exit':0,'cases':sum(map(int,counts)),'zero_case_not_a_test_pass':not counts})
explicit=(w/'original-provider-explicit.log').read_text();counts=re.findall(r'Success: ([0-9]+) tests passed[.]',explicit);assert counts and all(int(x)>0 for x in counts)
assert (w/'original-provider-explicit.exit').read_text().strip()=='0'
rows.append({'name':'providers-explicit-aspell','exit':0,'cases':sum(map(int,counts)),'module':'staged real Aspell provider'})
r={'scope':'Frozen Enchant2.8.19 Aspell-only real provider, supported relocatable build required by original tests; no optional provider breadth. Private UnitTest++2.0.0 PIC static SDK and its complete original tests, original432case API program plus explicit real Aspell provider program; default provider scan returned0with zero cases and is not a test pass. Four upstream CLI programs unexecuted because /usr prefix plus /etc sysconfdir causes their harness to exit0; not passes. Own real Aspell English/UTF8 personal persistence/session/refusal/recovery/CLI. No editor/GUI/Portuguese lexicon/general parser-security qualification.','compile_exit':0,'stage_exit':0,'private_sdk_original_cases':int(sdk[0]),'private_sdk_installed_to_system':False,'original_tests':rows,'original_program_scripts_not_executed':['misspelled-input.sh','unknown-option.sh','zero-arguments.sh','run-enchant-lsmod.sh'],'consumer':json.loads((w/'native-consumer.json').read_text()),'resources':{name:json.loads((w/('resource-tests2.json' if name=='tests' and (w/'resource-tests2.json').exists() else 'resource-'+name+'.json')).read_text()) for name in ['sdk','main','tests']},'artifacts':{str(p.relative_to(w/'compile')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (w/'compile').rglob('*') if p.is_file() and not p.is_symlink() and p.open('rb').read(4)==b'\x7fELF'},'stage_sha256':{str(p.relative_to('/stage')):hashlib.sha256(p.read_bytes()).hexdigest() for p in Path('/stage').rglob('*') if p.is_file() and not p.is_symlink()}}
(w/'stage-results.json').write_text(json.dumps(r,indent=2)+'\n')
PY

#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/stage-results.json ]]
export PYTHONDONTWRITEBYTECODE=1
ulimit -c 0
python3 - <<'PRE'
from pathlib import Path
import json
w=Path('/build');assert json.loads((w/'resource-main.json').read_text())['exit']==0
assert json.loads((w/'resource-tests2.json').read_text())['exit']==0
assert json.loads((w/'native-consumer.json').read_text())['provider']=='aspell'
assert not (w/'original-provider-explicit.log').exists()
PRE
mkdir -p /build/provider-direct/config
set +e
(cd /build/compile/tests && ENCHANT_CONFIG_DIR=/build/provider-direct/config LD_LIBRARY_PATH=/stage/usr/lib LIBTOOL=/build/compile/libtool /bin/bash /src/tests/run-test ./providers.test /stage/usr/lib/enchant-2/enchant_aspell.so) > /build/original-provider-explicit.log 2>&1
provider_exit=$?
set -e
printf '%s\n' "$provider_exit" > /build/original-provider-explicit.exit
[[ $provider_exit == 0 ]]
python3 - <<'COLLECT'
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
COLLECT

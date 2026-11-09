#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import hashlib,json,shutil,subprocess,tempfile
prefix=['chroot','/mnt/lfs'];env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':'/tmp','PYTHONDONTWRITEBYTECODE':'1'}
assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}','evolution-data-server'],text=True)=='install ok installed 3.60.2-1+toddy1'
for pc in ['libecal-2.0','libedataserver-1.2']:
    assert subprocess.check_output(prefix+['pkg-config','--modversion',pc],text=True).strip()=='3.60.2'
assert not subprocess.check_output(prefix+['dpkg','--audit'],text=True).strip();subprocess.run(prefix+['apt-get','check'],check=True)
work=Path('/mnt/lfs/sources/phase2/work/evolution-data-server-1');expected=json.loads((work/'stage-results.json').read_text())['consumer']
assert not Path('/mnt/lfs/stage').exists()
with tempfile.TemporaryDirectory(prefix='toddy-eds-',dir='/mnt/lfs/tmp') as directory:
    p=Path(directory);shutil.copyfile(work/'native-probe-4',p/'probe');(p/'probe').chmod(0o755)
    assert hashlib.sha256((p/'probe').read_bytes()).digest()==hashlib.sha256((work/'native-probe-4').read_bytes()).digest()
    native='/tmp/'+p.name+'/probe';libs=subprocess.check_output(prefix+['ldd',native],env=env,text=True)
    assert 'libecal-2.0.so.' in libs and '=> /usr/lib/libecal-2.0.so.' in libs
    assert 'libedbus-private.so => /usr/lib/evolution-data-server/libedbus-private.so' in libs
    assert '/stage/' not in libs
    consumer=json.loads(subprocess.check_output(prefix+[native],env=env,text=True,timeout=30));assert consumer==expected
code="""import gi,json
gi.require_version('EDataServer','1.2');gi.require_version('ECal','2.0')
from gi.repository import EDataServer,ECal
source=EDataServer.Source.new_with_uid('toddy-GI-synthetic-source',None)
assert source.get_uid()=='toddy-GI-synthetic-source'
component=ECal.Component.new_from_string('BEGIN:VEVENT\\r\\nUID:toddy-GI-event\\r\\nDTSTAMP:20261109T120000Z\\r\\nSUMMARY:Calendário local\\r\\nEND:VEVENT\\r\\n')
assert component and component.get_uid()=='toddy-GI-event'
print(json.dumps({'EDataServer1_2':True,'ECal2_0_with_ICalGLib4':True,'actual_source_and_component':True}))
"""
gi=json.loads(subprocess.check_output(prefix+['python3','-c',code],env=env,text=True,timeout=30))
Path('/var/log/toddy/phase2/evolution-data-server-installed-consumer.json').write_text(json.dumps({'scope':'Owned installed C/SDK/GI/calendar/source/refusal/prior-state/recovery only. Original101private-bus/client/storage passes reused; shared schema union/installed service activation/native GUI/remote accounts pending.','consumer':consumer,'GI':gi,'loaded_owned_private_library':True,'SDK_version':'3.60.2'},indent=2)+'\n')
PY

#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import hashlib,json,shutil,subprocess,tempfile
prefix=['chroot','/mnt/lfs'];env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':'/tmp','PYTHONDONTWRITEBYTECODE':'1'}
assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version} ${Architecture}','unicode-ucd'],text=True)=='install ok installed 17.0.0-1+toddy1 all'
assert not subprocess.check_output(prefix+['dpkg','--audit'],text=True).strip();subprocess.run(prefix+['apt-get','check'],check=True)
with tempfile.TemporaryDirectory(prefix='toddy-ucd-',dir='/mnt/lfs/tmp') as directory:
    p=Path(directory);shutil.copyfile('/opt/toddy-build/scripts/build/phase2/unicode-ucd-probe.py',p/'probe.py')
    actual=json.loads(subprocess.check_output(prefix+['python3','-B','/tmp/'+p.name+'/probe.py','/'],env=env,text=True,timeout=20))
expected=json.loads(Path('/mnt/lfs/sources/phase2/work/unicode-ucd-1/stage-results.json').read_text())['consumer'];assert actual==expected
record=json.loads(Path('/var/log/toddy/packages/unicode-ucd_17.0.0-1+toddy1_all.json').read_text());assert record['installed']
for name,row in record['payload'].items():
    if 'sha256' in row:assert hashlib.sha256((Path('/mnt/lfs')/name.lstrip('/')).read_bytes()).hexdigest()==row['sha256']
notices=Path('/mnt/lfs/usr/share/doc/unicode-ucd/source-notices');index=json.loads((notices/'index.json').read_text());assert len(index['sources'])==2
texts=[]
for source in index['sources']:
    assert source['notices']
    for row in source['notices']:
        data=(notices/row['sha256']).read_bytes();assert hashlib.sha256(data).hexdigest()==row['sha256'];texts.append(data)
assert any(b'Version 17.0.0' in text for text in texts) and any(text.startswith(b'UNICODE LICENSE V3') for text in texts)
Path('/var/log/toddy/phase2/unicode-ucd-installed-consumer.json').write_text(json.dumps({'scope':'Owned architecture-independent UCD17 data/version/40575scalar records/346block ranges/PT/emoji metadata/exact retained copyright and full Unicode3 license only; not Unicode conformance/rendering/native input acceptance.','consumer':actual,'architecture':'all','complete_pinned_notice_material_verified':True},indent=2)+'\n')
PY

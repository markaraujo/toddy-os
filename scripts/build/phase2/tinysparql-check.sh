#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import json,os,shutil,subprocess,tempfile
T=Path('/mnt/lfs');prefix=['chroot',str(T)];env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':'/tmp','PYTHONDONTWRITEBYTECODE':'1'}
for name,version in [('tinysparql','3.11.1-1+toddy1'),('sqlite','3.53.4-1+toddy1')]:assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}',name],text=True)=='install ok installed '+version
for name in ['tinysparql-3.0','tracker-sparql-3.0']:assert subprocess.check_output(prefix+['pkg-config','--modversion',name],text=True).strip()=='3.11.1'
assert not subprocess.check_output(prefix+['dpkg','--audit'],text=True).strip();subprocess.run(prefix+['apt-get','check'],check=True)
r=json.loads((T/'sources/phase2/work/tinysparql-1/stage-results.json').read_text());assert not (T/'stage').exists()
with tempfile.TemporaryDirectory(prefix='toddy-tinysparql-',dir=T/'tmp') as directory:
 p=Path(directory);os.chown(p,101,101);p.chmod(0o755);virtual='/tmp/'+p.name
 for name,relative in [('native-probe','native-probe'),('numeric-probe','numeric-5/probe')]:shutil.copyfile(T/'sources/phase2/work/tinysparql-1'/relative,p/name);(p/name).chmod(0o755)
 wrapper='set -euo pipefail; mount --make-rprivate /; mount -t tmpfs -o size=1m,nosuid,nodev tmpfs /mnt/lfs/dev; for name in null zero random urandom; do touch /mnt/lfs/dev/$name; mount --bind /dev/$name /mnt/lfs/dev/$name; done; exec chroot --userspec=101:101 /mnt/lfs "$@"'
 command=['unshare','--mount','--pid','--fork','--net','bash','-c',wrapper,'toddy-tinysparql']
 actual=json.loads(subprocess.check_output(command+[virtual+'/native-probe',virtual],env=env,text=True,timeout=30));assert actual==r['consumer']
 numeric=json.loads(subprocess.check_output(command+[virtual+'/numeric-probe'],env=env,text=True,timeout=30));assert numeric=={'typed_double_arithmetic_cases':4,'lossless_text_roundtrip_cases':4,'SQLite_settings_changed':False}
 gi=[]
 for namespace in ['Tracker','Tsparql']:
  code="import gi,json;namespace="+repr(namespace)+";gi.require_version(namespace,'3.0');m=__import__('gi.repository',fromlist=[namespace]);api=getattr(m,namespace);ontology=api.sparql_get_ontology_nepomuk();c=api.SparqlConnection.new(0,None,ontology,None);q=c.query('SELECT (1 AS ?value) WHERE {}',None);assert q.next(None) and q.get_integer(0)==1;assert not q.next(None);q.close();c.close();print(json.dumps({'namespace':namespace+'3.0','local_query':True}))"
  gi.append(json.loads(subprocess.check_output(command+['python3','-c',code],env=env,text=True,timeout=30)))
 libs=subprocess.check_output(prefix+['ldd',virtual+'/native-probe'],env=env,text=True);assert 'libtinysparql-3.0.so.0 => /usr/lib/libtinysparql-3.0.so.0' in libs and 'not found' not in libs
Path('/var/log/toddy/phase2/tinysparql-installed-consumer.json').write_text(json.dumps({'scope':'Actual installed UID101/private-device/no-route local RDF UTF8/persistence/malformed refusal/state retained/delete/reset two cycles, four typed numeric/lossless-text cases, separate Tracker/Tsparql GI query, shared ABI/pkg-config/APT0. Foundation SQLite unchanged. Four original lexical failures retained; no functional graphical-session/indexer/portal/grant/cancellation acceptance.','consumer':actual,'numeric':numeric,'GI_consumers':gi,'shared_library_resolution':True,'SQLite_unchanged':'3.53.4-1+toddy1'},indent=2)+'\n')
PY

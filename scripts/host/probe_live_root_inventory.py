#!/usr/bin/env python3
"""Inspect actual own native package archives and installed payload read-only."""
from pathlib import Path
import base64
import hashlib
import json
import os
import subprocess

os.chdir(Path(__file__).resolve().parents[2])
source = base64.b64encode(Path('scripts/build/h10/root_inventory.py').read_bytes()).decode()
script = r'''from pathlib import Path
import base64,hashlib,json,sys,tempfile,types
sys.path.insert(0,'/opt/toddy-build/scripts/build')
from package_backend import PackageBackend
root=Path('/mnt/lfs');backend=PackageBackend(root)
base=Path(tempfile.mkdtemp(prefix='toddy-root-inventory-',dir=root/'tmp'))
print('ROOT_INVENTORY_EVIDENCE '+str(base),flush=True)
module=types.ModuleType('root_inventory');module.__file__='/opt/toddy-build/scripts/build/h10/root_inventory.py'
exec(compile(base64.b64decode(SOURCE),module.__file__,'exec'),module.__dict__)
rows=backend.run('dpkg-query','-W','-f=${Package}_${Version}_${Architecture}\t${Status}\n',capture_output=True,text=True).stdout
records=[]
for line in rows.splitlines():
 stem,status=line.split('\t');assert status=='install ok installed'
 records.append(json.loads((Path('/var/log/toddy/packages')/(stem+'.json')).read_text()))
candidate=module.package_inventory(records)
candidate_data=(json.dumps(candidate,indent=2)+'\n').encode();candidate_path=base/'candidate-inventory.json';candidate_path.write_bytes(candidate_data)
print(json.dumps({'candidate_namespace_only':True,'package_records':len(records),'unique_copy_paths':len(candidate['names']),
 'regular_and_symlink_paths':sum(not row.get('directory') for row in candidate['entries'].values()),
 'fresh_directories':sorted(candidate['fresh_directories']), 'full_candidate_path':str(candidate_path),
 'full_candidate_sha256':hashlib.sha256(candidate_data).hexdigest(),'archive_and_installed_bytes_validation_pending':True,
 'complete_image_inventory':False},indent=2),flush=True)
inventory=module.inspect_installed(backend,Path('/var/log/toddy/packages'),Path('/var/cache/toddy/packages'))
data=(json.dumps(inventory,indent=2)+'\n').encode();(base/'inventory.json').write_bytes(data)
print(json.dumps({'verification':{k:v for k,v in inventory['verification'].items() if k!='record_sha256'},
 'unique_copy_paths':len(inventory['names']),'fresh_directories':inventory['fresh_directories'],
 'dbus_machine_id_entry':inventory['entries'].get('/var/lib/dbus/machine-id'),
 'complete_image_inventory':inventory['complete_image_inventory'],'pending_inputs':inventory['pending_inputs'],
 'full_inventory_path':str(base/'inventory.json'),'full_inventory_sha256':hashlib.sha256(data).hexdigest(),
 'full_inventory_bytes':len(data),'source_sha256':hashlib.sha256(base64.b64decode(SOURCE)).hexdigest(),
 'installed_target_modified':False,'active_build_inputs_synchronized':False},indent=2))
'''.replace('SOURCE', repr(source))
result = subprocess.run(['python3', 'scripts/host/vm.py', 'ssh',
    'source /opt/toddy-build/scripts/build/target.sh; guard_target && python3 -'],
    input=script, text=True, capture_output=True)
path = Path('.local/logs/h10-live-root-inventory-probe.json')
data = (json.dumps({'exit': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr}, indent=2) + '\n').encode()
sha = hashlib.sha256(data).hexdigest()
path.with_name(path.stem + '.' + sha + '.json').write_bytes(data)
path.write_bytes(data)
print(result.stdout, result.stderr)
print('exit', result.returncode, 'SHA256', sha)
result.check_returncode()

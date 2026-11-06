#!/usr/bin/env python3
"""Audit own CPython QA separation with real native archives, no installed edits."""
from pathlib import Path
import base64
import hashlib
import json
import os
import subprocess

os.chdir(Path(__file__).resolve().parents[2])
sources = {name: base64.b64encode((Path('scripts/build/h11') / name).read_bytes()).decode()
           for name in ('python_qa.py', 'audit_private_key_material.py')}
script = r'''from pathlib import Path
import base64,hashlib,json,shutil,subprocess,tempfile,types
root=Path('/mnt/lfs')
modules={}
for name,content in SOURCES.items():
 module=types.ModuleType(name);module.__file__='/opt/toddy-build/scripts/build/h11/'+name
 exec(compile(base64.b64decode(content),module.__file__,'exec'),module.__dict__)
 modules[name]=module
prefix=['chroot',str(root),'/usr/bin/env','-i','PATH=/usr/bin:/usr/sbin','LC_ALL=C']
identity=subprocess.check_output(prefix+['/usr/bin/dpkg-query','-W','-f=${Package}_${Version}_${Architecture} ${Status}','python'],text=True)
stem,status=identity.split(' ',1);assert status=='install ok installed'
record=json.loads((Path('/var/log/toddy/packages')/(stem+'.json')).read_text())
source=Path('/var/cache/toddy/packages')/(stem+'.deb')
with source.open('rb') as stream:sha=hashlib.file_digest(stream,'sha256').hexdigest()
assert sha==record['archive_sha256']
base=Path(tempfile.mkdtemp(prefix='toddy-python-qa-audit-',dir=root/'tmp'))
print('PYTHON_QA_AUDIT_FIXTURE '+str(base),flush=True)
try:
 archive=base/'source.deb';shutil.copyfile(source,archive)
 runtime=base/'runtime';qa=base/'qa'
 subprocess.run(prefix+['/usr/bin/dpkg-deb','--extract','/'+str(archive.relative_to(root)),'/'+str(runtime.relative_to(root))],check=True)
 audit=modules['audit_private_key_material.py'].scan
 before=audit(runtime)
 assert len(before['findings'])==15,before['findings']
 for finding in before['findings']:
  assert finding['path'].startswith('/usr/lib/python3.14/test/certdata/')
  assert record['payload'][finding['path']]['sha256']==finding['sha256']
 partition=modules['python_qa.py'].partition(runtime,qa)
 after=audit(runtime);qa_report=audit(qa)
 assert not after['findings'],after['findings']
 assert sorted(before['findings'],key=lambda r:r['path'])==sorted(qa_report['findings'],key=lambda r:r['path'])
 assert before['regular_files_scanned']==after['regular_files_scanned']+qa_report['regular_files_scanned']
 assert before['bytes_scanned']==after['bytes_scanned']+qa_report['bytes_scanned']
 print(json.dumps({'native_package':stem,'native_archive_sha256':sha,'partition':partition,
  'before':before,'runtime_after':after,'qa_after':qa_report,
  'all_matched_bytes_preserved_in_qa':True,'all_regular_file_count_and_bytes_preserved':True,
  'installed_changes':False,'native_package_transfer':False,'complete_image_credential_audit':False,
  'source_sha256':{name:hashlib.sha256(base64.b64decode(content)).hexdigest() for name,content in SOURCES.items()},
  'fixture_removed_after_checks':True},indent=2))
except BaseException:
 print('Preserved Python QA audit fixture:',base,flush=True)
 raise
else:shutil.rmtree(base)
'''.replace('SOURCES', repr(sources))
r = subprocess.run(['python3', 'scripts/host/vm.py', 'ssh',
                    'source /opt/toddy-build/scripts/build/target.sh; guard_target && python3 -'],
                   input=script, text=True, capture_output=True)
p = Path('.local/logs/h11-python-qa-key-audit-probe.json')
data = (json.dumps({'exit': r.returncode, 'stdout': r.stdout, 'stderr': r.stderr}, indent=2) + '\n').encode()
sha = hashlib.sha256(data).hexdigest()
p.with_name(p.stem + '.' + sha + '.json').write_bytes(data)
p.write_bytes(data)
print(r.stdout, r.stderr)
print('exit', r.returncode, 'SHA256', sha)
r.check_returncode()

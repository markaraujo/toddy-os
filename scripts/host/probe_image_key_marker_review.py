#!/usr/bin/env python3
"""Exercise marker review in an actual private native OpenSSL package closure."""
import base64
import hashlib
import json
from pathlib import Path
import subprocess
from vm import ssh_args

ROOT = Path(__file__).resolve().parents[2]
SOURCES = {name: base64.b64encode((ROOT / 'scripts/build/h11' / name).read_bytes()).decode()
           for name in ('review_image_key_markers.py', 'audit_private_key_material.py', 'require_gate.py')}
REMOTE = r'''
import base64,hashlib,json,os,re,shutil,subprocess,sys,tempfile
from pathlib import Path
subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
sys.path.insert(0,'/opt/toddy-build/scripts/build')
from package_backend import PackageBackend
root=Path('/mnt/lfs');backend=PackageBackend(root)
base=Path(tempfile.mkdtemp(prefix='toddy-key-marker-review-',dir=root/'tmp'))
print('KEY_MARKER_FIXTURE '+str(base),flush=True)
for name,body in SOURCES.items():(base/name).write_bytes(base64.b64decode(body))
sys.path.insert(0,str(base))
from review_image_key_markers import review, PREFIX, REVIEWED
def digest(path):
 with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
before=digest(root/'var/lib/dpkg/status')
try:
 raw=backend.run('dpkg-query','-W','-f=${Package}\t${Version}\t${Architecture}\t${Status}\t${Depends}\t${Pre-Depends}\n',capture_output=True,text=True).stdout
 installed={}
 for line in raw.splitlines():
  name,version,arch,state,depends,predepends=line.split('\t')
  if state=='install ok installed':installed[name]=(version,arch,depends+','+predepends)
 pending=['openssl','filesystem-layout'];selected=set()
 while pending:
  name=pending.pop()
  if name in selected:continue
  selected.add(name)
  for group in installed[name][2].split(','):
   if not group.strip():continue
   alternatives=[re.match(r'\s*([a-z0-9][a-z0-9+.-]*)',part).group(1) for part in group.split('|')]
   chosen=next((candidate for candidate in alternatives if candidate in installed),None)
   assert chosen is not None,group
   pending.append(chosen)
 cache=base/'archives';cache.mkdir();archives=[]
 for name in sorted(selected):
  version,arch,_=installed[name];stem=f'{name}_{version}_{arch}'
  record=json.loads((Path('/var/log/toddy/packages')/(stem+'.json')).read_text())
  source=Path('/var/cache/toddy/packages')/(stem+'.deb')
  assert record['installed'] and digest(source)==record['archive_sha256']
  copied=cache/source.name;shutil.copy2(source,copied);assert digest(copied)==record['archive_sha256']
  archives.append(copied)
 image=base/'image';db=image/'var/lib/dpkg';db.mkdir(parents=True);(db/'status').touch()
 with (base/'native-install.log').open('w') as log:
  backend.run('dpkg','--root=/'+str(image.relative_to(root)),'--unpack',
   *('/'+str(path.relative_to(root)) for path in archives),stdout=log,stderr=subprocess.STDOUT)
  backend.run('dpkg','--root=/'+str(image.relative_to(root)),'--configure','--pending',stdout=log,stderr=subprocess.STDOUT)
 def check():return review(backend,image)
 passed=check()
 assert passed['private_key_marker_check_passed'] and len(passed['raw_scan']['findings'])==6
 assert len(passed['qualified_document_examples'])==6 and not passed['unresolved_findings']
 assert not passed['whole_image_credential_audit_accepted'] and not passed['raw_findings_suppressed']
 cases=[]
 def report_failure(label,result,count):
  assert not result['private_key_marker_check_passed'] and len(result['unresolved_findings'])==count
  cases.append({'case':label,'unresolved_findings':result['unresolved_findings'],
    'qualified_examples':len(result['qualified_document_examples']),'marker_check_passed':False})
 manual=image/(PREFIX+'man3/PEM_read.pod')[1:];original=manual.read_bytes();metadata=manual.stat()
 manual.write_bytes(original+b'\nChanged private probe document.\n')
 report_failure('changed reviewed document',check(),1)
 manual.write_bytes(original);os.utime(manual,ns=(metadata.st_atime_ns,metadata.st_mtime_ns))
 duplicate=manual.with_name('unreviewed-copy.pod');shutil.copy2(manual,duplicate)
 report_failure('identical example at an unreviewed path',check(),1);duplicate.unlink()
 # Generate an actual disposable key, verify it parses, then prove rejection.
 # Keep contents private and out of both console and the evidence report.
 key=image/'root/private-probe-key.pem';key.parent.mkdir(mode=0o700,exist_ok=True)
 with key.open('xb') as stream:
  os.fchmod(stream.fileno(),0o600)
  backend.run('openssl','genpkey','-algorithm','ED25519',stdout=stream,stderr=subprocess.PIPE)
 backend.run('openssl','pkey','-in','/'+str(key.relative_to(root)),'-noout','-check',capture_output=True)
 report_failure('real generated private key',check(),1);key.unlink()
 fifo=image/'root/private-probe-fifo';os.mkfifo(fifo,0o600)
 special=check();assert not special['private_key_marker_check_passed'] and special['raw_scan']['special_nodes_not_read']==1
 cases.append({'case':'unread special node','marker_check_passed':False});fifo.unlink()
 def refused(label,call):
  try:call()
  except ValueError as error:cases.append({'case':label,'reason':str(error)})
  else:raise AssertionError(label+' was accepted')
 manual.chmod(0o600);refused('changed manual metadata',check);manual.chmod(metadata.st_mode & 0o7777)
 status=(db/'status').read_bytes()
 changed,count=re.subn(rb'(Package: openssl\nStatus: )install ok installed',rb'\1deinstall ok config-files',status)
 assert count==1
 (db/'status').write_bytes(changed);refused('unconfigured OpenSSL image identity',check);(db/'status').write_bytes(status)
 bad_records=base/'bad-records';bad_records.mkdir()
 version,arch,_=installed['openssl'];record_name=f'openssl_{version}_{arch}.json'
 bad_record=json.loads((Path('/var/log/toddy/packages')/record_name).read_text());bad_record['archive_sha256']='0'*64
 (bad_records/record_name).write_text(json.dumps(bad_record))
 refused('changed own archive provenance',lambda:review(backend,image,records=bad_records))
 refused('installed builder is not a staged image',lambda:review(backend,root))
 gate=subprocess.run([sys.executable,'-B',str(base/'review_image_key_markers.py'),str(image)],
  env=dict(os.environ,PYTHONPATH='/opt/toddy-build/scripts/build'),capture_output=True,text=True)
 assert gate.returncode!=0 and 'H11 requires H10 completed and H11 in_progress' in gate.stderr
 cases.append({'case':'premature production CLI','exit':gate.returncode,'required_gate':'H10 completed and H11 in_progress'})
 final=check();assert final['raw_scan']['findings']==passed['raw_scan']['findings'] and final['private_key_marker_check_passed']
 assert digest(root/'var/lib/dpkg/status')==before
 result={'fixture':str(base),'configured_packages':sorted(selected),'positive':passed,'negative_cases':cases,
  'native_install_log':(base/'native-install.log').read_text(),
  'native_install_log_sha256':digest(base/'native-install.log'),'builder_status_sha256':before,
  'installed_target_modified':False,'component_sha256':digest(base/'review_image_key_markers.py'),
  'real_private_key_rejected':True,'whole_image_credential_audit_accepted':False,'release_image_or_boot_accepted':False}
 (base/'result.json').write_text(json.dumps(result,indent=2)+'\n')
 print('KEY_MARKER_RESULT '+json.dumps(result),flush=True)
 shutil.rmtree(base)
except BaseException:
 print('PRESERVED_KEY_MARKER_FIXTURE '+str(base),flush=True)
 raise
'''


def main():
    result = subprocess.run(ssh_args() + ['python3 -B -'],
        input='SOURCES=' + repr(SOURCES) + '\n' + REMOTE, text=True, capture_output=True, timeout=600)
    raw = (result.stdout + result.stderr).encode()
    sha = hashlib.sha256(raw).hexdigest()
    path = ROOT / '.local/logs' / ('h11-image-key-marker-review-' + sha + '.log')
    path.write_bytes(raw)
    print(json.dumps({'exit': result.returncode, 'report': str(path), 'sha256': sha}))
    if result.returncode:
        print(result.stdout + result.stderr)
        raise SystemExit(result.returncode)
    report = json.loads(next(line.removeprefix('KEY_MARKER_RESULT ') for line in result.stdout.splitlines()
                             if line.startswith('KEY_MARKER_RESULT ')))
    print(json.dumps({'configured_packages': len(report['configured_packages']),
        'qualified_examples': len(report['positive']['qualified_document_examples']),
        'negative_cases': len(report['negative_cases']), 'real_private_key_rejected': report['real_private_key_rejected'],
        'whole_image_credential_audit_accepted': False}))


if __name__ == '__main__':
    main()

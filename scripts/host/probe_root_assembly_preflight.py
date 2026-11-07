#!/usr/bin/env python3
"""Exercise actual native assembly refusals without bypassing foundation gates."""
import base64
import hashlib
import json
from pathlib import Path
import subprocess
from vm import ssh_args

ROOT = Path(__file__).resolve().parents[2]
SOURCES = {str(path.relative_to(ROOT)): base64.b64encode(path.read_bytes()).decode()
           for path in sorted((ROOT / 'scripts/build').rglob('*.py'))}
SOURCES['config/live-account-baseline.json'] = base64.b64encode(
    (ROOT / 'config/live-account-baseline.json').read_bytes()).decode()
REMOTE = r'''
import base64,hashlib,json,os,shutil,subprocess,sys,tempfile
from pathlib import Path
subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
root=Path('/mnt/lfs');base=Path(tempfile.mkdtemp(prefix='toddy-root-assembly-',dir=root/'tmp'))
print('ASSEMBLY_FIXTURE '+str(base),flush=True)
project=base/'project'
for name,body in SOURCES.items():
 path=project/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(base64.b64decode(body))
sys.path.insert(0,str(project/'scripts/build/h10'))
import assemble_root as assembly
from package_backend import PackageBackend
backend=PackageBackend(root)
def digest(path):
 with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
before=digest(root/'var/lib/dpkg/status');cases=[]
try:
 script=project/'scripts/build/h10/assemble_root.py'
 for release,required in ((False,'H10 requires H09 completed and H10 in_progress'),
                          (True,'H11 requires H10 completed and H11 in_progress')):
  image=base/('release-image' if release else 'intermediate-image');work=base/(image.name+'-evidence')
  result=subprocess.run([sys.executable,'-B',str(script),str(image),str(work)]+(['--release'] if release else []),
    capture_output=True,text=True)
  assert result.returncode!=0 and required in result.stderr,(result.returncode,result.stderr)
  assert not image.exists() and not work.exists()
  cases.append({'case':'production release gate' if release else 'production H10 gate',
    'exit':result.returncode,'required_gate':required,'output_created':False})
  compression=project/'scripts/build/h10/compress_root.py'
  result=subprocess.run([sys.executable,'-B',str(compression),str(base/'absent-assembly.json'),str(work),
                        '--epoch','1793923200']+(['--release'] if release else []),capture_output=True,text=True)
  assert result.returncode!=0 and required in result.stderr,(result.returncode,result.stderr)
  assert not work.exists()
  cases.append({'case':'production compression release gate' if release else 'production compression H10 gate',
    'exit':result.returncode,'required_gate':required,'output_created':False})
  initramfs=project/'scripts/build/h10/initramfs_archive.py'
  result=subprocess.run([sys.executable,'-B',str(initramfs),str(base/'absent-compression.json'),str(work),
                        '--media-id','0'*64]+(['--release'] if release else []),capture_output=True,text=True)
  assert result.returncode!=0 and required in result.stderr,(result.returncode,result.stderr)
  assert not work.exists()
  cases.append({'case':'production initramfs release gate' if release else 'production initramfs H10 gate',
    'exit':result.returncode,'required_gate':required,'output_created':False})
 def refuse(label,image,work):
  try:assembly.validate_destinations(root,image,work)
  except ValueError as error:cases.append({'case':label,'reason':str(error)})
  else:raise AssertionError(label+' was accepted')
 refuse('installed root as image',root,base/'unused-evidence')
 existing=base/'existing-image';existing.mkdir();(existing/'sentinel').write_text('preserve\n')
 refuse('existing image',existing,base/'unused-evidence');assert (existing/'sentinel').read_text()=='preserve\n'
 existing_work=base/'existing-evidence';existing_work.mkdir()
 refuse('existing evidence',base/'unused-image',existing_work)
 alias=base/'redirect';alias.symlink_to(existing)
 refuse('redirected image',alias,base/'unused-evidence')
 refuse('overlapping image/evidence',base/'unused-image',base/'unused-image/evidence')
 public=base/'unprotected';public.mkdir();public.chmod(0o777)
 refuse('unprotected output parent',public/'image',public/'evidence')
 # A real component preflight reaches the known unfinished H07 payload
 # obligation. It cannot copy a root or grant any later milestone credit.
 image=base/'readiness-image';work=base/'readiness-evidence'
 try:assembly.assemble(backend,image,work,repository=project)
 except ValueError as error:
  assert str(error)=='Owned package bytes changed: /usr/share/info/dir',str(error)
  reason=str(error)
 else:raise AssertionError('Unfinished H07 inventory unexpectedly passed; inspect before new assembly')
 journal=json.loads((work/'assembly.json').read_text())
 assert not image.exists() and not journal['assembled'] and not journal['release_accepted']
 assert len(journal['actions'])==1 and journal['actions'][0]['step']=='source-inventory'
 assert journal['actions'][0]['finished'] is None and journal['failure']==reason
 assert digest(root/'var/lib/dpkg/status')==before
 report={'fixture':str(base),'negative_cases':cases,'actual_readiness_refusal':reason,
  'durable_failed_preflight':journal,'builder_status_sha256':before,'installed_target_modified':False,
  'assembler_sha256':digest(script),'complete_assembly_verified':False,'native_boot_verified':False}
 print('ASSEMBLY_RESULT '+json.dumps(report),flush=True)
 shutil.rmtree(base)
except BaseException:
 print('PRESERVED_ASSEMBLY_FIXTURE '+str(base),flush=True)
 raise
'''


def main():
    result = subprocess.run(ssh_args() + ['python3 -B -'], input='SOURCES=' + repr(SOURCES) + '\n' + REMOTE,
                            text=True, capture_output=True, timeout=600)
    raw = (result.stdout + result.stderr).encode()
    sha = hashlib.sha256(raw).hexdigest()
    path = ROOT / '.local/logs' / ('h10-root-assembly-preflight-' + sha + '.log')
    path.write_bytes(raw)
    print(json.dumps({'exit': result.returncode, 'report': str(path), 'sha256': sha}))
    if result.returncode:
        print(result.stdout + result.stderr)
        raise SystemExit(result.returncode)
    report = json.loads(next(line.removeprefix('ASSEMBLY_RESULT ') for line in result.stdout.splitlines()
                             if line.startswith('ASSEMBLY_RESULT ')))
    print(json.dumps({'negative_cases': len(report['negative_cases']),
        'actual_readiness_refusal': report['actual_readiness_refusal'], 'complete_assembly_verified': False}))


if __name__ == '__main__':
    main()

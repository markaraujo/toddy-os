"""Bind original LocalSearch inputs for native tests without copying/rebuilding."""
from pathlib import Path
import fcntl,hashlib,json,os,subprocess

SELECTED={'test_cli_search':6,'test_cli_inhibit':4,'test_cli_reset':4,
          'dbus-access':1,'exec':1,'fs-read':1,'fs-read-trunc':1,'fs-write':1,'net-access':1}
SOURCE_SHA='7b39a6c28a8acf2b172f15b2fb5ee7c7a3764c447c2f4a14caa239b7ebe61942'
RECIPE_SHA='f25eb13e03a5b1fde6763e0bea50e923bec82ebae12cbc596d0cbb2e060d2499'

def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def manifest(base):
 return {str(p.relative_to(base)):digest(p) for p in base.rglob('*') if p.is_file() and not p.is_symlink()}

def select_tests(rows):
 selected=[r for name in SELECTED for r in rows if r['name']==name]
 assert len(selected)==len(SELECTED) and {r['name'] for r in selected}==set(SELECTED)
 for r in selected:
  assert r['protocol']=='exitcode' and r['cmd'][0]=='/usr/bin/python3'
  assert r['workdir'] is None and r['timeout'] in (30,120)
  assert r['cmd'][1].startswith('/src/tests/functional-tests/')
  assert 'localsearch:'+('malice' if r['name'] not in ('test_cli_search','test_cli_inhibit','test_cli_reset') else 'functional') in r['suite']
 return selected

def main():
 assert os.geteuid()==0
 subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
 lock=open('/var/log/toddy/build/build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
 assert not Path('/var/log/toddy/build/input-sync.running').exists()
 l=Path('/var/log/toddy/phase2');w=Path('/mnt/lfs/sources/phase2/work/localsearch-1');s=Path('/mnt/lfs/sources/phase2/inputs/localsearch-3.11.1')
 receipt=l/'localsearch-native-fixture-1.json'
 assert not receipt.exists(),'Inspect existing receipt; no uncertain replay'
 assert (l/'localsearch-1.exit').read_text().strip()=='1' and (l/'localsearch-collect-2.exit').read_text().strip()=='0'
 assert digest(s/'toddy-build.sh')==RECIPE_SHA
 prepared=json.loads((s/'toddy-prepared.json').read_text());assert prepared['source_sha256']==SOURCE_SHA and not prepared['source_patches']
 r=json.loads((w/'stage-results.json').read_text());assert r['compile_exit']==r['stage_exit']==0
 assert len(r['artifacts'])==186 and len(r['stage_sha256'])==133
 assert len(r['original_tests'])==13 and all(t['returncode']==0 and t['result']=='OK' for t in r['original_tests'])
 for name,sha in r['artifacts'].items():assert digest(w/'compile'/name)==sha
 assert manifest(w/'stage')==r['stage_sha256']
 config=(w/'compile/config-miners.h').read_text().splitlines()
 assert '#define HAVE_LANDLOCK' in config and '#define HAVE_LIBSECCOMP' in config
 selected=select_tests(json.loads((w/'original-registered-tests.json').read_text()))
 for row in selected:
  for path in row['cmd'][1:]:
   actual=(s/path.removeprefix('/src/')) if path.startswith('/src/') else w/path.removeprefix('/build/')
   assert actual.exists() and not actual.is_symlink()
 kernel=Path('/mnt/lfs/boot/vmlinuz-7.1.8-toddy')
 assert digest(kernel)=='18c4d9e6a64554296d8e9a037c2383e7426a0cf155b6d757d0693fce0d087ad1'
 # All generated resources, original tests, libraries and data are read-only
 # native inputs; preserve full manifests without a duplicate source/build tree.
 proof={'state':'complete','scope':'Native fixture inputs prepared only; no native runtime or promotion acceptance.',
        'source_sha256':SOURCE_SHA,'original_recipe_sha256':RECIPE_SHA,
        'source_path':'/sources/phase2/inputs/localsearch-3.11.1','work_path':'/sources/phase2/work/localsearch-1',
        'source_files':manifest(s),'compile_files':manifest(w/'compile'),'stage_files':r['stage_sha256'],
        'selected_tests':selected,'expected_cases':SELECTED,'kernel_sha256':digest(kernel),
        'prepared_sha256':digest(s/'toddy-prepared.json'),'original_report_sha256':digest(w/'stage-results.json')}
 native=Path('/mnt/lfs/sources/phase2/native-fixtures/localsearch-1.json')
 assert not native.exists() and not native.is_symlink()
 native.parent.mkdir(parents=True,exist_ok=True)
 with native.open('x') as f:json.dump(proof,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
 with receipt.open('x') as f:json.dump(proof,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
 print(json.dumps({'state':'complete','receipt':str(receipt),'source_files':len(proof['source_files']),'compile_files':len(proof['compile_files']),'programs':len(selected),'expected_cases':sum(SELECTED.values()),'receipt_sha256':digest(receipt)}))
if __name__=='__main__':main()

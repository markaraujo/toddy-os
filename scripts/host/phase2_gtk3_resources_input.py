#!/usr/bin/env python3
"""Freeze qualified existing resources for private GTK3 integration checks."""
import subprocess
import phase2_vm


def main():
    script=(phase2_vm.ROOT/'scripts/build/phase2/gtk3_resources_build.py').read_text()
    remote='recipe='+repr(script)+'\n'+r'''
from pathlib import Path
import fcntl,hashlib,json,os,shutil,subprocess
subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
lock=open('/var/log/toddy/build/build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
sysroot=Path('/mnt/lfs');log=Path('/var/log/toddy/phase2')
assert (log/'gtk3-1.exit').read_text().strip()=='0'
result=json.loads((sysroot/'sources/phase2/work/gtk3-1/test-results.json').read_text())
assert result['original_rgba_cases']==4 and result['staged_consumer_exit']==result['gi_exit']==result['private_schema_exit']==0
import sys
sys.path.insert(0,'/opt/toddy-build/scripts/build/phase2')
from verify_stage import inspect_stage
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
old=json.loads(Path('/var/log/toddy/packages/gtk_4.22.4-1+toddy2_amd64.json').read_text())
assert old['installed'] and old['version']=='4.22.4-1+toddy2'
assert sha(Path('/var/cache/toddy/packages/gtk_4.22.4-1+toddy2_amd64.deb'))==old['archive_sha256']
base=sysroot/'usr/share/glib-2.0/schemas'
cache=base/'gschemas.compiled'
assert sha(cache)==old['payload']['/usr/share/glib-2.0/schemas/gschemas.compiled']['sha256']
inputs={p.name:sha(p) for p in base.iterdir() if p.is_file() and p.name!='gschemas.compiled'}
transaction=json.loads((log/'desktop-resources-transaction.json').read_text())
assert transaction['state']=='complete' and inputs==transaction['schema_inputs']
source=sysroot/'sources/phase2/inputs/gtk3-resources-1';work=sysroot/'sources/phase2/work/gtk3-resources-1'
assert not source.exists() and not work.exists(), 'Reconcile existing resource preparation, never replay'
assert os.statvfs(sysroot).f_bavail*os.statvfs(sysroot).f_frsize>=16*1024**3+128*1024**2
original=sysroot/'sources/phase2/work/gtk3-1/stage';before=inspect_stage(original)
source.mkdir();(source/'stock').mkdir()
for p in base.iterdir():
    assert p.is_file() and not p.is_symlink()
    shutil.copy2(p,source/'stock'/p.name)
assert {p.name:sha(p) for p in (source/'stock').iterdir() if p.name!='gschemas.compiled'}==inputs
# Hardlinks retain qualified bytes without another large physical copy. The
# compiler sees this input read-only and has no writable alias to the old work.
shutil.copytree(original,source/'gtk3-stage',copy_function=os.link,symlinks=True)
assert inspect_stage(source/'gtk3-stage')==before==inspect_stage(original)
record={'scope':'Frozen owned stock schemas/cache plus qualified GTK3 stage; read-only input alias, no system/resource mutation',
        'old_gtk_version':old['version'],'old_gtk_archive_sha256':old['archive_sha256'],
        'old_cache_sha256':sha(cache),'stock_inputs':inputs,
        'gtk3_stage':before,'recipe_sha256':hashlib.sha256(recipe.encode()).hexdigest()}
(source/'toddy-build.py').write_text(recipe)
(source/'toddy-resources.json').write_text(json.dumps(record,indent=2)+'\n')
work.mkdir();os.chown(work,101,101)
print(json.dumps({'input':str(source),'work':str(work),'stock_files':len(inputs),
                  'gtk3_stage_entries':len(before['entries']),'old_gtk_version':old['version']}))
'''
    compile(remote,'<gtk3-resource-input>','exec')
    destination=phase2_vm.ROOT/'.local/phase2/gtk3-resources-input.log'
    with destination.open('xb') as log:
        result=subprocess.run(phase2_vm.ssh_args()+['python3 -'],input=remote.encode(),stdout=log,stderr=subprocess.STDOUT)
    destination.with_suffix('.exit').write_text(str(result.returncode)+'\n')
    raise SystemExit(result.returncode)


if __name__=='__main__':main()

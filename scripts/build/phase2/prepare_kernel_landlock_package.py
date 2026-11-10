"""Prepare native archive from qualified scratch stage, no duplicate stage."""
from pathlib import Path
import json,os,subprocess
from qualify_kernel_landlock_stage import qualify,W,L,digest,ROOT
T=Path('/mnt/lfs');VERSION='7.1.8-1+toddy1'
assert os.getuid()==0
subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
r,inspection=qualify()
assert subprocess.check_output(['chroot',str(T),'dpkg-query','-W','-f=${Status} ${Version}','linux-kernel'],text=True)=='install ok installed 7.1.8-1'
original=json.loads(Path('/var/log/toddy/packages/linux-kernel_7.1.8-1_amd64.json').read_text())
for name in ['vmlinuz','config','System.map']:
 path='/boot/'+name+'-7.1.8-toddy';assert digest(T/path.lstrip('/'))==original['payload'][path]['sha256']
assert digest(Path('/var/cache/toddy/packages/linux-kernel_7.1.8-1_amd64.deb'))==original['archive_sha256']
assert not Path('/var/cache/toddy/packages/linux-kernel_'+VERSION+'_amd64.deb').exists()
destination=T/'sources/stage/phase2-linux-kernel-landlock';receipt=L/'kernel-landlock-native-stage-bind-1.json'
assert not destination.exists() and not receipt.exists() and not receipt.with_suffix('.part').exists(),'Inspect existing promotion/archive/package; never replay'
assert os.statvfs(T).f_bavail*os.statvfs(T).f_frsize>=16*1024**3+100*1024**2
assert os.statvfs(W).f_bavail*os.statvfs(W).f_frsize>=128*1024**2
state={'state':'bind-intended','source':str(W/'stage'),'destination':str(destination),'source_inode':(W/'stage').stat().st_ino,'verified_manifest_sha256':inspection['manifest_sha256']}
def save():
 p=receipt.with_suffix('.part');p.write_text(json.dumps(state,indent=2)+'\n');p.replace(receipt)
save();destination.mkdir();subprocess.run(['mount','--bind',str(W/'stage'),str(destination)],check=True)
assert destination.stat().st_ino==state['source_inode'];os.chown(destination,0,0)
state['state']='bound';save()
subprocess.run(['python3',str(ROOT/'scripts/build/stage_package.py'),'linux-kernel',VERSION,str(destination),'--source','linux-7.1.8.tar.xz','--recipe',str(ROOT/'scripts/build/phase2/linux-kernel-landlock-package.sh'),'--depends','kmod, filesystem-layout','--compression-threads','2'],cwd=ROOT,check=True)
state.update(state='archive-prepared',archive_sha256=digest(Path('/var/cache/toddy/packages/linux-kernel_'+VERSION+'_amd64.deb')));save()

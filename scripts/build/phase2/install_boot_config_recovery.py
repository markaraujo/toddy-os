"""Update only the native owner of the measured boot menu, preserving old source."""
from pathlib import Path
import json,os,shutil,subprocess
from boot_config_recovery import render,base_render
from qualify_kernel_landlock_stage import L,digest,ROOT
T=Path('/mnt/lfs');stage=T/'sources/stage/phase2-boot-config-landlock';receipt=L/'boot-config-recovery-input-1.json'
assert os.getuid()==0
subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
passed=json.loads(Path('/var/log/toddy/build/b02-linux-kernel-landlock-install.success.json').read_text());assert passed['recipe_exit']==passed['postcheck_exit']==0
assert subprocess.check_output(['chroot',str(T),'dpkg-query','-W','-f=${Status} ${Version}','toddy-boot-config'],text=True)=='install ok installed 0.1-1'
assert not stage.exists() and not receipt.exists() and not receipt.with_suffix('.part').exists(),'Reconcile prior stage/package; no replay'
fs=subprocess.check_output(['blkid','-s','UUID','-o','value','/dev/vdb4'],text=True).strip();part=subprocess.check_output(['blkid','-s','PARTUUID','-o','value','/dev/vdb4'],text=True).strip()
old=base_render(fs,part);assert (T/'etc/toddy/grub.cfg').read_text()==old,'Preserve local edits; diagnose before modifying owned conffile'
assert os.readlink(T/'boot/grub/grub.cfg')=='../../etc/toddy/grub.cfg'
backups=json.loads((L/'kernel-landlock-installed-check-1.json').read_text())['rollback_artifacts']
for name,sha in backups.items():assert digest(T/name)==sha
new=render(fs,part);data={'state':'stage-intended','filesystem_uuid':fs,'partition_uuid':part,'old_config_sha256':digest(T/'etc/toddy/grub.cfg'),'new_config_sha256':__import__('hashlib').sha256(new.encode()).hexdigest(),'old_package':'0.1-1','new_package':'0.1-2+toddy1'}
p=receipt.with_suffix('.part');p.write_text(json.dumps(data,indent=2)+'\n');p.replace(receipt)
for d in ['boot/grub','etc/toddy','usr/share/doc/toddy-boot-config']:(stage/d).mkdir(parents=True,exist_ok=True)
(stage/'etc/toddy/grub.cfg').write_text(new);(stage/'boot/grub/grub.cfg').symlink_to('../../etc/toddy/grub.cfg')
shutil.copyfile(ROOT/'LICENSES/LFS-MIT.txt',stage/'usr/share/doc/toddy-boot-config/copyright')
shutil.copyfile(ROOT/'config/books.lock.json',stage/'usr/share/doc/toddy-boot-config/book-sources.json')
(stage/'usr/share/doc/toddy-boot-config/profile.txt').write_text('Experimental Phase2 measured builder boot profile. Default kernel has Landlock; separate foundation recovery entry retains old qualified image and identical20module payloads. UUIDs are builder-specific, not portable installer output. Configuration source is LFS13.1/H09 plus versioned Toddy recovery renderer; original code MIT. Actual installed-system/rollback boots require separate evidence.\n')
subprocess.run(['chroot',str(T),'grub-script-check','/'+str((stage/'etc/toddy/grub.cfg').relative_to(T))],check=True)
subprocess.run(['python3',str(ROOT/'scripts/build/stage_package.py'),'toddy-boot-config','0.1-2+toddy1',str(stage),'--architecture','all','--depends','grub, linux-kernel (= 7.1.8-1+toddy1)','--conffile','/etc/toddy/grub.cfg','--recipe',str(ROOT/'scripts/build/phase2/boot-config-landlock-install.sh'),'--install'],cwd=ROOT,check=True)

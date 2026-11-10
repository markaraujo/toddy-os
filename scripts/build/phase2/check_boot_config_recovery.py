"""Verify menu source/syntax/ownership, while keeping actual boot acceptance separate."""
from pathlib import Path
import json,os,subprocess
from boot_config_recovery import render
from qualify_kernel_landlock_stage import L,digest
T=Path('/mnt/lfs');cmd=['chroot',str(T)];V='0.1-2+toddy1'
assert subprocess.check_output(cmd+['dpkg-query','-W','-f=${Status} ${Version}','toddy-boot-config'],text=True)=='install ok installed '+V
inputs=json.loads((L/'boot-config-recovery-input-1.json').read_text());text=(T/'etc/toddy/grub.cfg').read_text();assert text==render(inputs['filesystem_uuid'],inputs['partition_uuid']) and digest(T/'etc/toddy/grub.cfg')==inputs['new_config_sha256']
assert text.count('menuentry ')==2 and text.count('/boot/vmlinuz-7.1.8-toddy-foundation ')==1 and text.count('set default=0')==1
assert os.readlink(T/'boot/grub/grub.cfg')=='../../etc/toddy/grub.cfg'
subprocess.run(cmd+['grub-script-check','/boot/grub/grub.cfg'],check=True)
record=json.loads(Path('/var/log/toddy/packages/toddy-boot-config_'+V+'_all.json').read_text());assert record['installed']
for name,row in record['payload'].items():
 p=T/name.lstrip('/');assert p.lstat().st_mode==row['mode'] and p.lstat().st_uid==row['uid']==0 and p.lstat().st_gid==row['gid']==0
 if 'sha256' in row:assert digest(p)==row['sha256']
 elif 'symlink' in row:assert os.readlink(p)==row['symlink']
for name in ['/boot/grub/grub.cfg','/etc/toddy/grub.cfg']:
 assert subprocess.check_output(cmd+['dpkg-query','-S',name],text=True).strip()=='toddy-boot-config: '+name
for path in ['boot/vmlinuz-7.1.8-toddy','boot/vmlinuz-7.1.8-toddy-foundation']:assert (T/path).stat().st_size>0
old=T/'etc/toddy/grub.cfg.dpkg-old';backup=None
if old.exists():assert digest(old)==inputs['old_config_sha256'];backup={'path':'/etc/toddy/grub.cfg.dpkg-old','sha256':digest(old),'scope':'Native conffile backup, retained as generated configuration recovery data'}
assert not subprocess.check_output(cmd+['dpkg','--audit'],text=True).strip();subprocess.run(cmd+['apt-get','check'],check=True)
p=L/'boot-config-recovery-check-1.json';assert not p.exists()
p.write_text(json.dumps({'scope':'Two owned boot entries/default retained/source/syntax/native package/conffile ownership/APT0 only. Actual installed and foundation-recovery boots pending.','version':V,'config_sha256':inputs['new_config_sha256'],'native_conffile_backup':backup,'menu_entries':2,'default':0},indent=2)+'\n')

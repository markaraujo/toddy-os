"""Check native payload/rollback ownership; installed boot is a subsequent gate."""
from pathlib import Path
import json,os,subprocess
from qualify_kernel_landlock_stage import W,L,digest,KERNEL_SHA
T=Path('/mnt/lfs');version='7.1.8-1+toddy1';cmd=['chroot',str(T)]
assert subprocess.check_output(cmd+['dpkg-query','-W','-f=${Status} ${Version}','linux-kernel'],text=True)=='install ok installed '+version
record=json.loads(Path('/var/log/toddy/packages/linux-kernel_'+version+'_amd64.json').read_text());assert record['installed'] and record['version']==version
for name,row in record['payload'].items():
 p=T/name.lstrip('/');assert p.lstat().st_mode==row['mode'],name
 if 'sha256' in row:assert digest(p)==row['sha256'],name
 elif 'symlink' in row:assert os.readlink(p)==row['symlink'],name
 assert p.lstat().st_uid==row['uid']==0 and p.lstat().st_gid==row['gid']==0
r=json.loads((W/'kernel-stage-1.json').read_text())
for name,sha in r['backups'].items():assert digest(T/name)==sha
assert digest(T/'boot/vmlinuz-7.1.8-toddy')==KERNEL_SHA
old=json.loads(Path('/var/log/toddy/packages/linux-kernel_7.1.8-1_amd64.json').read_text());assert digest(Path('/var/cache/toddy/packages/linux-kernel_7.1.8-1_amd64.deb'))==old['archive_sha256']
assert not subprocess.check_output(cmd+['dpkg','--audit'],text=True).strip();subprocess.run(cmd+['apt-get','check'],check=True)
assert os.statvfs(T).f_bavail*os.statvfs(T).f_frsize>=16*1024**3 and os.statvfs(W).f_bavail*os.statvfs(W).f_frsize>=128*1024**2
p=L/'kernel-landlock-installed-check-1.json';assert not p.exists()
p.write_text(json.dumps({'scope':'Native package/payload/ownership/APT0 and retained foundation archive/rollback artifacts only. Boot entry and installed Systemd/rollback boots pending.','version':version,'payload_entries':len(record['payload']),'kernel_sha256':KERNEL_SHA,'rollback_artifacts':r['backups'],'target_free_bytes':os.statvfs(T).f_bavail*os.statvfs(T).f_frsize,'scratch_free_bytes':os.statvfs(W).f_bavail*os.statvfs(W).f_frsize},indent=2)+'\n')

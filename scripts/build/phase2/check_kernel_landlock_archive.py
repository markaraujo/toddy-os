"""Read the complete built Debian payload and prove no native install occurred."""
from pathlib import Path
import hashlib,json,os,subprocess,tarfile
from qualify_kernel_landlock_stage import W,L,digest,KERNEL_SHA
T=Path('/mnt/lfs');V='7.1.8-1+toddy1';archive=Path('/var/cache/toddy/packages/linux-kernel_'+V+'_amd64.deb')
r=json.loads(Path('/var/log/toddy/packages/linux-kernel_'+V+'_amd64.json').read_text());assert not r['installed'] and digest(archive)==r['archive_sha256']
assert subprocess.check_output(['chroot',str(T),'dpkg-query','-W','-f=${Status} ${Version}','linux-kernel'],text=True)=='install ok installed 7.1.8-1'
expected=r['payload'];seen={}
p=subprocess.Popen(['dpkg-deb','--fsys-tarfile',str(archive)],stdout=subprocess.PIPE)
with tarfile.open(fileobj=p.stdout,mode='r|') as t:
 for m in t:
  name='/'+m.name.removeprefix('./').rstrip('/')
  if name in ['/.','/']:assert m.uid==m.gid==0;continue
  assert name in expected and name not in seen,name
  row=expected[name];assert m.uid==row['uid']==0 and m.gid==row['gid']==0 and m.mode==(row['mode']&0o7777),name
  if m.isfile():actual=hashlib.file_digest(t.extractfile(m),'sha256').hexdigest();assert actual==row['sha256'],name
  elif m.islnk():actual=seen['/'+m.linkname.removeprefix('./')];assert actual==row['sha256'],name
  elif m.issym():assert m.linkname==row['symlink'];actual=m.linkname
  else:assert m.isdir() and row['directory'];actual=True
  seen[name]=actual
assert p.wait()==0 and set(seen)==set(expected)
s=json.loads((W/'kernel-stage-1.json').read_text())
for name,sha in s['backups'].items():assert expected['/'+name]['sha256']==sha
assert expected['/boot/vmlinuz-7.1.8-toddy']['sha256']==KERNEL_SHA
old=json.loads(Path('/var/log/toddy/packages/linux-kernel_7.1.8-1_amd64.json').read_text())
for name in ['vmlinuz','config','System.map']:
 path='/boot/'+name+'-7.1.8-toddy';assert digest(T/path.lstrip('/'))==old['payload'][path]['sha256']
assert os.statvfs(T).f_bavail*os.statvfs(T).f_frsize>=16*1024**3 and os.statvfs(W).f_bavail*os.statvfs(W).f_frsize>=128*1024**2
receipt=L/'kernel-landlock-archive-verified-1.json';assert not receipt.exists()
receipt.write_text(json.dumps({'scope':'Full actual archive payload/modes/root ownership verified, rollback artifacts retained; kernel not installed','archive_sha256':r['archive_sha256'],'archive_bytes':archive.stat().st_size,'payload_entries':len(expected),'kernel_sha256':KERNEL_SHA,'target_free_bytes':os.statvfs(T).f_bavail*os.statvfs(T).f_frsize,'scratch_free_bytes':os.statvfs(W).f_bavail*os.statvfs(W).f_frsize},indent=2)+'\n')
print(receipt.read_text())

#!/usr/bin/env python3
"""Roundtrip the real minimal /init runtime archive in private native storage.

Public fixture digests are intentionally not a claim of a live root or boot.
"""
from pathlib import Path
import base64
import hashlib
import json
import os
import subprocess

os.chdir(Path(__file__).resolve().parents[2])
sources = {name: base64.b64encode((Path('scripts/build/h10') / name).read_bytes()).decode()
           for name in ('initramfs_runtime.py', 'initramfs_archive.py', 'live_init.sh', 'live_media.sh')}
script = r'''from pathlib import Path
import base64,gzip,hashlib,json,os,shutil,stat,subprocess,sys,tempfile,types
root=Path('/mnt/lfs');base=Path(tempfile.mkdtemp(prefix='toddy-initramfs-archive-',dir=root/'tmp'))
print('INITRAMFS_ARCHIVE_FIXTURE '+str(base),flush=True)
for name,content in SOURCES.items():
 (base/name).write_bytes(base64.b64decode(content))
for name in ('initramfs_runtime','initramfs_archive'):
 module=types.ModuleType(name)
 module.__file__='/opt/toddy-build/scripts/build/h10/'+name+'.py'
 sys.modules[name]=module
 exec(compile((base/(name+'.py')).read_bytes(),module.__file__,'exec'),module.__dict__)
archive=sys.modules['initramfs_archive']
media_id=hashlib.sha256(b'private archive identity fixture').hexdigest()
root_digest=hashlib.sha256(b'opaque fixture, no Squashfs root exists in this test').hexdigest()
epoch=1793923200
try:
 reports=[]
 for name in ('first','second'):
  reports.append(archive.assemble(root,base/name,Path('/var/log/toddy/packages'),base/'live_init.sh',base/'live_media.sh',media_id,root_digest,epoch))
 assert reports[0]['cpio_sha256']==reports[1]['cpio_sha256']
 assert reports[0]['gzip_sha256']==reports[1]['gzip_sha256']
 raw=(base/'first/initramfs.cpio').read_bytes()
 damaged=bytearray(raw);needle=b'Toddy live init must run as PID 1'
 assert raw.count(needle)==1
 damaged[raw.index(needle)]=ord('X')
 try:archive.validate_newc(bytes(damaged),reports[0]['entries'],epoch)
 except ValueError as error: corruption=str(error)
 else:raise AssertionError('Modified executable accepted')
 try:archive.validate_newc(raw[:100],reports[0]['entries'],epoch)
 except ValueError as error: truncation=str(error)
 else:raise AssertionError('Truncated archive accepted')
 try:archive.assemble(root,base/'first',Path('/var/log/toddy/packages'),base/'live_init.sh',base/'live_media.sh',media_id,root_digest,epoch)
 except ValueError as error: existing=str(error)
 else:raise AssertionError('Existing stage replaced')
 assert (base/'first/initramfs.cpio').read_bytes()==raw
 output=base/'extracted';output.mkdir()
 r=subprocess.run(['chroot',str(root),'/usr/bin/env','-i','PATH=/usr/bin:/usr/sbin','LC_ALL=C','/bin/bash','-c',
  'cd "$1" && exec bsdcpio -i -d -m --quiet','extract','/'+str(output.relative_to(root))],input=raw,capture_output=True)
 assert r.returncode==0,(r.returncode,r.stderr)
 expected=reports[0]['entries']
 actual={'.'}|{p.relative_to(output).as_posix() for p in output.rglob('*')}
 assert actual==set(expected)
 for name,entry in expected.items():
  path=output/name;info=path.lstat()
  assert info.st_mode==entry['mode'] and info.st_uid==info.st_gid==0,name
  assert [os.major(info.st_rdev),os.minor(info.st_rdev)]==entry['rdev'],name
  if stat.S_ISREG(info.st_mode):body=path.read_bytes()
  elif stat.S_ISLNK(info.st_mode):body=os.readlink(path).encode()
  else:body=b''
  assert hashlib.sha256(body).hexdigest()==entry['body_sha256'],name
 # Ordinary invocation must refuse before attempting live mounts. This also
 # verifies the extracted shell/loader/library paths actually execute.
 r=subprocess.run(['chroot',str(output),'/init'],env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C'},text=True,capture_output=True)
 assert r.returncode==1 and 'no mounts attempted' in r.stderr,(r.returncode,r.stderr)
 digest_check=subprocess.check_output(['chroot',str(output),'/bin/bash','-c',
  'source /usr/lib/toddy/live_media.sh; sha256sum /etc/toddy-live/media-id'],text=True,
  env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C'})
 assert digest_check.split()[0]==hashlib.sha256((media_id+'\n').encode()).hexdigest()
 assert (output/'etc/toddy-live/rootfs.sha256').read_text()==root_digest+'\n'
 print(json.dumps({'entry_count':reports[0]['entry_count'],'native_files':len(reports[0]['runtime']['files']),
  'gzip_bytes':reports[0]['gzip_bytes'],'cpio_sha256':reports[0]['cpio_sha256'],'gzip_sha256':reports[0]['gzip_sha256'],
  'same_filesystem_two_fresh_stages_identical':True,'native_extract_bytes_modes_owners_devices_links':True,
  'extracted_native_non_pid1_init_refusal':{'exit':r.returncode,'stderr':r.stderr.strip()},
  'negative_cases':{'modified_init':corruption,'truncation':truncation,'existing_stage':existing},
  'embedded_metadata_readback':True,'native_helper_load':True,'root_image_exists':False,'kernel_boot':False,
  'source_sha256':{name:hashlib.sha256(base64.b64decode(value)).hexdigest() for name,value in SOURCES.items()},
  'archive_tools':reports[0]['archive_tools'],'manifest':reports[0],
  'manifest_sha256':hashlib.sha256((base/'first/manifest.json').read_bytes()).hexdigest(),
  'fixture_removed_after_checks':True},indent=2))
except BaseException:
 print('Preserved initramfs archive fixture:',base,flush=True)
 raise
else:shutil.rmtree(base)
'''.replace('SOURCES', repr(sources))
r = subprocess.run(['python3', 'scripts/host/vm.py', 'ssh',
                    'source /opt/toddy-build/scripts/build/target.sh; guard_target && python3 -'],
                   input=script, text=True, capture_output=True)
p = Path('.local/logs/h10-native-initramfs-archive-probe.json')
p.parent.mkdir(parents=True, exist_ok=True)
data = (json.dumps({'exit': r.returncode, 'stdout': r.stdout, 'stderr': r.stderr}, indent=2) + '\n').encode()
sha = hashlib.sha256(data).hexdigest()
p.with_name(p.stem + '.' + sha + '.json').write_bytes(data)
p.write_bytes(data)
print(r.stdout, r.stderr)
print('exit', r.returncode, 'SHA256', sha)
r.check_returncode()

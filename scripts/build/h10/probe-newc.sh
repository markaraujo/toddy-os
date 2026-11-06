#!/bin/bash
# Private native archive experiment only; no live image or H10 acceptance.
source /opt/toddy-build/scripts/build/h06/common.sh
chroot_run <<'INNER'
set -euo pipefail
dpkg-query -S /usr/bin/bsdcpio | grep -F 'libarchive: ' >&2
python3 - <<'PY'
from pathlib import Path
import gzip,hashlib,json,os,stat,subprocess,tempfile
with tempfile.TemporaryDirectory(prefix='toddy-newc-') as directory:
 root=Path(directory);source=root/'input';source.mkdir(mode=0o755);source.chmod(0o755)
 (source/'empty').mkdir(mode=0o755)
 (source/'init').write_bytes(b'#!/bin/sh\nexit 0\n');(source/'init').chmod(0o755)
 (source/'payload').write_bytes(b'native hardlink payload\n');(source/'payload').chmod(0o640)
 os.link(source/'payload',source/'hardlink')
 (source/'symlink').symlink_to('payload')
 unicode_name='ola\u0301 arquivo\nsecond line'
 (source/unicode_name).write_bytes(b'UTF-8 and NUL-separated names\n')
 (source/unicode_name).chmod(0o644)
 for path in [source,*source.rglob('*')]:os.utime(path,(1793836800,1793836800),follow_symlinks=False)
 names=['.']+sorted(str(p.relative_to(source)) for p in source.rglob('*'))
 archive=root/'root.cpio'
 with archive.open('wb') as stream:
  subprocess.run(['bsdcpio','-o','--null','--format=newc','--owner','0:0','--quiet'],cwd=source,input=b'\0'.join(n.encode() for n in names)+b'\0',stdout=stream,check=True)
 raw=archive.read_bytes();offset=0;entries={}
 while True:
  assert raw[offset:offset+6]==b'070701','Kernel newc magic differs'
  fields=[int(raw[offset+i:offset+i+8],16) for i in range(6,110,8)]
  name_raw=raw[offset+110:offset+110+fields[11]]
  assert name_raw.endswith(b'\0') and b'\0' not in name_raw[:-1]
  name=name_raw[:-1].decode();offset=(offset+110+fields[11]+3)&~3
  body=raw[offset:offset+fields[6]];offset=(offset+fields[6]+3)&~3
  if name=='TRAILER!!!':break
  assert not name.startswith('/') and '..' not in Path(name).parts
  assert fields[2:4]==[0,0]
  entries[name]={'fields':fields,'body':body}
 assert set(entries)==set(names)
 assert stat.S_IMODE(entries['init']['fields'][1])==0o755
 assert stat.S_IMODE(entries['payload']['fields'][1])==0o640
 assert entries['payload']['fields'][0]==entries['hardlink']['fields'][0]
 assert entries['payload']['fields'][4]==entries['hardlink']['fields'][4]==2
 assert entries['symlink']['body']==b'payload'
 assert entries[unicode_name]['body']==(source/unicode_name).read_bytes()
 assert not any(raw[offset:]),'Unexpected non-padding data after newc trailer'
 output=root/'output';output.mkdir()
 subprocess.run(['bsdcpio','-i','-d','-m','--no-preserve-owner','--quiet'],cwd=output,input=raw,check=True)
 assert (output/'payload').read_bytes()==(source/'payload').read_bytes()
 assert (output/'hardlink').stat().st_ino==(output/'payload').stat().st_ino
 assert stat.S_IMODE((output/'init').stat().st_mode)==0o755
 assert stat.S_IMODE((output/'payload').stat().st_mode)==0o640
 assert os.readlink(output/'symlink')=='payload'
 assert (output/unicode_name).read_bytes()==(source/unicode_name).read_bytes()
 compressed=subprocess.check_output(['gzip','-n','-c',str(archive)])
 assert gzip.decompress(compressed)==raw
 print(json.dumps({'tool':subprocess.check_output(['bsdcpio','--version'],text=True).strip(),'format':'newc 070701','entries':len(entries),'hardlinks':True,'symlinks':True,'modes':True,'unicode_and_newline_names':True,'root_ownership':True,'gzip_roundtrip':True,'archive_sha256':hashlib.sha256(raw).hexdigest(),'gzip_sha256':hashlib.sha256(compressed).hexdigest(),'installed_changes':False,'kernel_boot_validated':False}))
PY
INNER

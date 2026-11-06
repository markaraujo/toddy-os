#!/usr/bin/env python3
"""Verify native media identity/hash handling with private opaque-file fixtures.

This checks the integrity component, not ISO/Squashfs format or kernel boot.
"""
from pathlib import Path
import base64
import hashlib
import json
import os
import subprocess

os.chdir(Path(__file__).resolve().parents[2])
helper=base64.b64encode(Path('scripts/build/h10/live_media.sh').read_bytes()).decode()
script=r'''from pathlib import Path
import base64,hashlib,json,os,shutil,subprocess,tempfile
root=Path('/mnt/lfs');work=Path(tempfile.mkdtemp(prefix='toddy-media-integrity-',dir=root/'tmp'))
helper=work/'live_media.sh';helper.write_bytes(base64.b64decode(HELPER))
media=work/'media';media.mkdir();(media/'live').mkdir()
media_id=hashlib.sha256(b'private identity fixture').hexdigest()
payload=b'Harmless integrity fixture, not a Squashfs image.\n'
digest=hashlib.sha256(payload).hexdigest()
(media/'.toddy-media-id').write_text(media_id+'\n');image=media/'live/rootfs.squashfs';image.write_bytes(payload)
reports=[]
injection='$(touch /'+str((work/'unexpected-execution').relative_to(root))+')'
def verify(label,expected,location=media,identity=media_id,sha=digest):
 r=subprocess.run(['chroot',str(root),'/usr/bin/env','-i','PATH=/usr/bin:/usr/sbin','LC_ALL=C','/bin/bash','--noprofile','--norc','-c','source "$1"; toddy_verify_media "$2" "$3" "$4"','probe','/'+str(helper.relative_to(root)),'/'+str(location.relative_to(root)),identity,sha],text=True,capture_output=True)
 assert r.returncode==expected,(label,r.returncode,r.stdout,r.stderr)
 reports.append({'case':label,'exit':r.returncode,'diagnostic':r.stderr.strip()})
try:
 verify('matching identity and exact bytes',0)
 image.write_bytes(payload[:-1]+b'X');verify('modified payload',1);image.write_bytes(payload)
 verify('wrong identity',1,identity='0'*64)
 verify('malformed expected digest',1,sha=injection)
 (media/'.toddy-media-id').write_text(injection+'\n');verify('media text never evaluated',1);(media/'.toddy-media-id').write_text(media_id+'\n')
 image.unlink();verify('missing root payload',1)
 (work/'outside').write_bytes(payload);image.symlink_to(work/'outside');verify('redirected root file',1);image.unlink();image.write_bytes(payload)
 (media/'live').rename(media/'saved-live');(media/'live').symlink_to('saved-live');verify('redirected payload directory',1);(media/'live').unlink();(media/'saved-live').rename(media/'live')
 alias=work/'redirected-media';alias.symlink_to(media);verify('redirected media root',1,location=alias)
 assert (work/'outside').read_bytes()==payload
 assert not (work/'unexpected-execution').exists()
 verify('restored input succeeds',0)
 print(json.dumps({'cases':reports,'source_sha256':hashlib.sha256(helper.read_bytes()).hexdigest(),'native_bash_and_sha256':True,'actual_iso_or_squashfs_test':False,'fixture_removed_after_checks':True,'injection_sentinel_absent':True},indent=2))
except BaseException:
 print('Preserved media-integrity fixture:',work)
 raise
else:shutil.rmtree(work)
'''.replace('HELPER',repr(helper))
r=subprocess.run(['python3','scripts/host/vm.py','ssh','source /opt/toddy-build/scripts/build/target.sh; guard_target && python3 -'],input=script,text=True,capture_output=True)
p=Path('.local/logs/h10-native-media-integrity-probe.json');p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps({'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr},indent=2)+'\n')
print(r.stdout,r.stderr);print('exit',r.returncode,'SHA256',hashlib.sha256(p.read_bytes()).hexdigest());r.check_returncode()

"""Bind real kernel/diagnostic evidence to the authenticated rollback-ready stage."""
from pathlib import Path
import hashlib,json,subprocess
from verify_stage import inspect_stage
W=Path('/mnt/lfs/sources/phase2/work/kernel-landlock-1');L=Path('/var/log/toddy/phase2');ROOT=Path('/opt/toddy-build')
KERNEL_SHA='18c4d9e6a64554296d8e9a037c2383e7426a0cf155b6d757d0693fce0d087ad1'
def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def qualify():
 assert (L/'kernel-landlock-stage-2.exit').read_text().strip()=='0'
 expected=(ROOT/'scripts/build/phase2/kernel_landlock_stage.py').read_text().replace("assert not list(s.iterdir()) and not (w/'kernel-stage-1.json').exists()","assert list(s.iterdir()) and not (w/'kernel-stage-1.json').exists()").replace("subprocess.run(['dpkg-deb','--extract',str(archive),str(s)],check=True)",'')
 assert json.loads((L/'kernel-landlock-stage-2.job.json').read_text())['command'][-1]==expected
 r=json.loads((W/'kernel-stage-1.json').read_text());assert r['stage_exit']==0 and r['candidate_artifacts']['arch/x86/boot/bzImage']==KERNEL_SHA and len(r['modules'])==20
 actual=inspect_stage(W/'stage');assert actual['manifest_sha256']=='b2a4f80a29a37407b693dbf3d4d459ea08f921ee6d00a0d69849771047d37322'
 assert {n:v['sha256'] for n,v in actual['entries'].items() if 'sha256' in v}==r['stage_sha256']
 assert json.loads((L/'kernel-landlock-lower-retained-1.json').read_text())['unchanged_entries']==111558
 assert digest(W/'baseline.json')=='d0e66e8e3cc2260d35242a1dca634e72bfd6bcd3d63a5bd94bac591a173114bf'
 proof=json.loads((L/'kernel-landlock-native-acceptance-1.json').read_text());assert proof['kernel_sha256']==KERNEL_SHA and proof['result']['complete'] and {x['firmware'] for x in proof['result']['runs']}=={'bios','uefi'}
 assert proof['diagnostic_source_sha256']==digest(ROOT/'scripts/build/phase2/kernel_landlock_init.c')
 for x in proof['result']['runs']:assert x['exit']==0 and x['kernel_boot_verified'] and not x['target_disks_attached']
 return r,actual
if __name__=='__main__':
 r,m=qualify();print(json.dumps({'stage_entries':len(m['entries']),'regular_files':len(r['stage_sha256']),'candidate_kernel_sha256':KERNEL_SHA}))

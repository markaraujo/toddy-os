"""Native-only LocalSearch original functional and extractor-denial programs."""
import base64,hashlib,json,os,re,subprocess,termios,zlib
from pathlib import Path
ACCEPTED_FIXTURE = None
CONSUMER_SOURCE = None

def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def output(args):return subprocess.check_output(args,text=True,timeout=15).strip()
def main():
 assert os.geteuid()==0 and os.uname().release=='7.1.8-toddy'
 assert Path('/proc/1/comm').read_text().strip()=='systemd'
 assert output(['systemd-detect-virt','--vm']) in ['kvm','qemu']
 device=output(['findmnt','-n','-o','SOURCE','/']);assert re.fullmatch('/dev/[a-z0-9]+',device)
 parent=output(['lsblk','-ndo','PKNAME',device]);assert re.fullmatch('[a-z0-9]+',parent)
 assert output(['lsblk','-dnro','SERIAL','/dev/'+parent])=='TODDY-BOOT-TEST'
 assert output(['blkid','-s','LABEL','-o','value',device])=='TODDY_LFS'
 assert isinstance(ACCEPTED_FIXTURE,dict) and ACCEPTED_FIXTURE['state']=='complete'
 descriptor=Path('/sources/phase2/native-fixtures/localsearch-1.json')
 assert not descriptor.is_symlink() and descriptor.stat().st_uid==0
 assert digest(descriptor)==ACCEPTED_FIXTURE['fixture_sha256']
 fixture=json.loads(descriptor.read_text());assert fixture['state']=='complete'
 assert digest(Path('/boot/vmlinuz-7.1.8-toddy'))==fixture['kernel_sha256']
 source=Path(fixture['source_path']);work=Path(fixture['work_path'])
 assert str(source)=='/sources/phase2/inputs/localsearch-3.11.1' and str(work)=='/sources/phase2/work/localsearch-1'
 assert not source.is_symlink() and not work.is_symlink()
 def verify():
  for base,key in [(source,'source_files'),(work/'compile','compile_files'),(work/'stage','stage_files')]:
   actual={str(p.relative_to(base)):digest(p) for p in base.rglob('*') if p.is_file() and not p.is_symlink()}
   assert actual==fixture[key]
 verify()
 assert isinstance(CONSUMER_SOURCE,str) and CONSUMER_SOURCE
 # All bind mounts live only in this disposable native child namespace.
 # Original source/build resources remain read-only; runtime data uses ext4.
 result=subprocess.run(['unshare','--mount','--pid','--net','--fork','--kill-child=SIGKILL','python3','-B','-c',CONSUMER_SOURCE],input=json.dumps(fixture),capture_output=True,text=True,timeout=600)
 verify()
 runs=[{'name':'native-LocalSearch-original-programs','exit':result.returncode,'stdout':result.stdout,'stderr':result.stderr}]
 report={'scope':'Native7.1.8/Systemd real LocalSearch original CLI search/inhibit/reset plus six extractor malicious modules. Private session bus and upstream volume-monitor fixture; no GNOME/widget/installed-package/physical acceptance.','kernel':os.uname().release,'pid1':'systemd','runs':runs,'input_manifests_unchanged':True,'expected_programs':9,'expected_cases':20}
 if result.returncode==0:
  details=json.loads(result.stdout);assert details['all_selected_passed'] and details['programs']==9 and details['cases']==20
  report['details']=details
 raw=json.dumps(report,sort_keys=True).encode();encoded=base64.b64encode(zlib.compress(raw,9)).decode();chunks=[encoded[i:i+1024] for i in range(0,len(encoded),1024)]
 success=result.returncode==0
 fd=os.open('/dev/ttyS1',os.O_WRONLY|os.O_NOCTTY)
 attrs=termios.tcgetattr(fd);attrs[0]=attrs[1]=attrs[3]=0
 attrs[2]|=termios.CLOCAL|termios.CREAD;attrs[4]=attrs[5]=termios.B115200
 termios.tcsetattr(fd,termios.TCSANOW,attrs)
 with os.fdopen(fd,'w',buffering=1) as evidence:
  for i,chunk in enumerate(chunks):print('TODDY_B02_RUNTIME_DATA',i,chunk,file=evidence,flush=True)
  print('TODDY_B02_RUNTIME_RESULT',json.dumps({'kernel':os.uname().release,'all_selected_exits_zero':success,'report_sha256':hashlib.sha256(raw).hexdigest(),'chunks':len(chunks)}),file=evidence,flush=True)
  termios.tcdrain(evidence.fileno())
 assert success,'Actual native failure retained'
if __name__=='__main__':
 try:main()
 except Exception as error:
  print('TODDY_B02_RUNTIME_FAIL',type(error).__name__,str(error),flush=True)
  raise

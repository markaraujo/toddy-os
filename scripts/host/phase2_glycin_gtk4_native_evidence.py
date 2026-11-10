#!/usr/bin/env python3
"""Bind real native results to exact committed payload and immutable stage/core inputs."""
from pathlib import Path
import base64,hashlib,json,shlex,subprocess
import phase2_vm
from phase2_native_glycin import compressed_payload
from phase2_native_report import decode

def main():
 root=phase2_vm.ROOT;context=root/'.local/phase2/native-glycin-gtk4-runtime-1'
 s=json.loads((context/'result.json').read_text());r=json.loads((context/'native-report.json').read_text())
 assert s['phase']=='native-report-recorded' and s['backing_unchanged'] and s['native_selected_passed']
 decoded,summary,recovered=decode((context/'serial.log').read_text(errors='replace'));assert decoded==r and summary==s['summary'] and recovered==s['recovered_protocol_markers']
 c=json.loads(subprocess.check_output(['docker','inspect',s['container_id']],text=True))[0]
 assert c['State']['Status']=='exited' and c['State']['ExitCode']==0 and not c['State']['OOMKilled'] and c['Config']['Labels']['toddy.boot-test']==s['run_id']
 paths=['scripts/host/phase2-native-glycin-gtk4-probe.py','scripts/build/phase2/glycin-gtk4-native-consumer.py']
 for path in paths:assert (root/path).read_bytes()==subprocess.check_output(['git','show',s['commit']+':'+path],cwd=root)
 body=(root/paths[0]).read_text()
 for name,value in [('CONSUMER_SOURCE',(root/paths[1]).read_text()),('ACCEPTED_FIXTURE',s['accepted'])]:
  assert body.count(name+' = None')==1;body=body.replace(name+' = None',name+' = '+repr(value))
 probe=body.encode();bootstrap=compressed_payload(probe)
 assert hashlib.sha256(probe).hexdigest()==s['probe_sha256'] and hashlib.sha256(bootstrap).hexdigest()==s['payload_sha256']
 prefix='type=11,value=io.systemd.credential.binary:toddy.boot-probe='
 for command in [s['command'],c['Config']['Cmd']]:
  payloads=[v[len(prefix):] for v in command if v.startswith(prefix)];assert len(payloads)==1 and base64.b64decode(payloads[0],validate=True)==bootstrap
 assert r['kernel']=='7.1.8-toddy' and r['pid1']=='systemd' and summary['all_selected_exits_zero']
 assert r['stage_file_hashes']==s['accepted']['stage_sha256'] and r['installed_core_files_unchanged']==s['accepted']['installed_core_sha256']
 assert len(r['runs'])==1 and r['runs'][0]['exit']==0 and r['runs'][0]['stderr']==''
 expected={'sandbox':'BWRAP','installed_default_loader_paths':True,'source_image_pixel_cases':4,'GDK_texture_PNG_pixel_roundtrips':4,'malformed_refusals':2,'recovery_cycles':2,'display_or_widgets_tested':False}
 assert json.loads(r['runs'][0]['stdout'])==expected
 proof={'state':'native-companion-conversion-qualified','scope':r['scope'],'commit':s['commit'],'probe_sha256':s['probe_sha256'],'payload_sha256':s['payload_sha256'],'report_sha256':summary['report_sha256'],'consumer':expected,'stage_sha256':r['stage_file_hashes'],'installed_core_sha256':r['installed_core_files_unchanged'],'container_exit':0,'OOMKilled':False,'backing_unchanged':True}
 code="""from pathlib import Path
import fcntl,hashlib,json
lock=open('/var/log/toddy/build/build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
proof=PROOF;report=REPORT
assert hashlib.sha256(json.dumps(report,sort_keys=True).encode()).hexdigest()==proof['report_sha256']
w=Path('/mnt/lfs/sources/phase2/work/glycin-gtk4-1/stage')
for name,sha in proof['stage_sha256'].items():assert hashlib.sha256((w/name).read_bytes()).hexdigest()==sha
for name,sha in proof['installed_core_sha256'].items():assert hashlib.sha256((Path('/mnt/lfs')/name.lstrip('/')).read_bytes()).hexdigest()==sha
for name,value in [('glycin-gtk4-native-qualification.json',proof),('glycin-gtk4-native-runtime-1.json',report)]:
 p=Path('/var/log/toddy/phase2')/name;data=(json.dumps(value,sort_keys=True)+'\\n').encode()
 if p.exists():assert p.read_bytes()==data
 else:
  with p.open('xb') as f:f.write(data)
print(json.dumps(proof))
""".replace('PROOF',repr(proof)).replace('REPORT',repr(r))
 result=subprocess.run(phase2_vm.ssh_args()+['python3 -c '+shlex.quote(code)],capture_output=True,text=True);print(result.stdout,result.stderr);assert result.returncode==0
if __name__=='__main__':main()

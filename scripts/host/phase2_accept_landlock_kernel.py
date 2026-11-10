#!/usr/bin/env python3
"""Import only actual completed token-bound no-disk diagnostic evidence."""
from pathlib import Path
import hashlib,json,shlex,subprocess
import phase2_vm as vm

def main():
 base=vm.ROOT/'.local/phase2/native-kernel-landlock-1';intent=json.loads((base/'intent.json').read_text());r=json.loads((base/'result.json').read_text())
 assert r['complete'] and json.loads((base/'driver.exit.json').read_text())=={'exit':0} and len(r['runs'])==2
 token=intent['prepared']['token'];kernel=intent['prepared']['kernel_sha256']
 assert kernel=='18c4d9e6a64554296d8e9a037c2383e7426a0cf155b6d757d0693fce0d087ad1'
 assert hashlib.sha256((base/'bzImage').read_bytes()).hexdigest()==kernel
 assert hashlib.sha256((vm.ROOT/'scripts/build/phase2/kernel_landlock_init.c').read_bytes()).hexdigest()==intent['prepared']['source_sha256']
 for mode in ['bios','uefi']:
  state=json.loads((base/mode/'terminal.json').read_text());assert not state['Running'] and state['ExitCode']==0 and not state['OOMKilled']
  entry=next(x for x in r['runs'] if x['firmware']==mode);raw=(base/mode/'serial.log').read_bytes();assert hashlib.sha256(raw).hexdigest()==entry['serial_sha256']
  text=raw.decode(errors='replace');assert text.splitlines().count('TODDY_LANDLOCK_OK token='+token+' firmware='+mode)==1 and 'TODDY_LANDLOCK_FAIL' not in text and 'Kernel panic' not in text and not entry['target_disks_attached']
 proof={'scope':'Only validated actual BIOS+UEFI no-disk diagnostic boots; no installed-system/desktop acceptance','kernel_sha256':kernel,'diagnostic_source_sha256':intent['prepared']['source_sha256'],'source_commit':intent['source_commit'],'result':r,'result_sha256':hashlib.sha256((base/'result.json').read_bytes()).hexdigest()}
 body=json.dumps(proof,indent=2)+'\n'
 code='body='+repr(body)+'\n'+'''from pathlib import Path
import fcntl,subprocess
subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
lock=open('/var/log/toddy/build/build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
p=Path('/var/log/toddy/phase2/kernel-landlock-native-acceptance-1.json')
if p.exists():assert p.read_text()==body
else:
 with p.open('x') as f:f.write(body)
print('Actual native evidence verified/imported; no boot/package replay')
'''
 subprocess.run(vm.ssh_args()+['python3 -c '+shlex.quote(code)],check=True)
if __name__=='__main__':main()

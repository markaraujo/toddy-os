"""Real private test-key generation/public derivation/refusal, no retained key data."""
from pathlib import Path
import json,subprocess,sys,tempfile
p=Path(sys.argv[1]);keygen=p/'ssh-keygen'
r=subprocess.run([str(p/'ssh'),'-V'],capture_output=True,text=True,timeout=10,check=True);assert r.stderr.startswith('OpenSSH_10.5p1, ')
with tempfile.TemporaryDirectory(prefix='toddy-keygen-',dir='/build') as directory:
 d=Path(directory);key=d/'key'
 subprocess.run([str(keygen),'-q','-t','ed25519','-N','','-C','public fixture','-f',str(key)],check=True,capture_output=True,timeout=20)
 assert key.stat().st_mode&0o777==0o600
 derived=subprocess.run([str(keygen),'-y','-f',str(key)],check=True,capture_output=True,text=True,timeout=10).stdout.split()[:2]
 assert derived==(d/'key.pub').read_text().split()[:2] and derived[0]=='ssh-ed25519'
 invalid=d/'invalid';invalid.write_text('Toddy malformed fixture\n');invalid.chmod(0o600)
 r=subprocess.run([str(keygen),'-y','-f',str(invalid)],capture_output=True,text=True,timeout=10);assert r.returncode!=0 and 'invalid format' in r.stderr
 recovery=subprocess.run([str(keygen),'-l','-f',str(key)],check=True,capture_output=True,text=True,timeout=10);assert 'ED25519' in recovery.stdout
 derived=None
assert not Path(directory).exists()
print(json.dumps({'version':'10.5p1','ephemeral_ed25519_generate_derive_match':True,'malformed_key_refused':True,'recovery_fingerprint':True,'temporary_keys_removed':True,'key_material_retained':False,'scope':'Private keygen fixture tool only; no SSH network/client/server qualification'}))

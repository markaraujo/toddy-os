"""Qualified CLI only; root trust generation/provider/update remains separate."""
from pathlib import Path
import json,os,subprocess,sys,tempfile
script=Path(sys.argv[1])/'usr/sbin/make-ca'
with tempfile.TemporaryDirectory(prefix='make-ca-cli-') as directory:
 env={**os.environ,'TMPDIR':directory}
 runs=[]
 for args,success in [(['--version'],True),(['--help'],True),(['--toddy-invalid-option'],False)]:
  r=subprocess.run([str(script),*args],env=env,capture_output=True,text=True,timeout=10)
  assert (r.returncode==0)==success
  if args==['--version']:assert '1.16.1' in r.stdout
  if args==['--help']:assert '--certdata' in r.stdout and '--rebuild' in r.stdout and '--destdir' in r.stdout
  runs.append({'args':args,'exit':r.returncode})
assert not Path(directory).exists()
print(json.dumps({'version':'1.16.1','CLI_runs':runs,'temporary_data_removed':True,'scope':'CLI/version/invalid option only; no CA/PKCS11/default trust/update/recovery acceptance'}))

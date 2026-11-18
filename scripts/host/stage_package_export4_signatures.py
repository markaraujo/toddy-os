#!/usr/bin/env python3
"""Only the fresh export4 public packet to the fixed native stdout-verifying entry."""
import json,os,subprocess,sys
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import stage_package_export3_signatures as first

def main(generation=4):
    if type(generation) is not int or generation not in (4,5,6,7):raise ValueError('Only fixed export4/export5/export6/export7 entry')
    if sys.argv[1:]:raise SystemExit('No arbitrary path/action/signing-context arguments')
    context=first.fixed_context(generation);output=context/'native-signatures-verified.json'
    if os.path.lexists(output):raise ValueError('Preserve existing export4 result; no replay')
    raw=first.packet(generation);owned=first.candidate.owned();first.candidate.bases()
    result=subprocess.run(first.candidate.ssh()+['bash /opt/toddy-build/scripts/build/phase2/image_native.sh signatures-export'+str(generation)],input=raw,
        stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=180,check=True)
    if len(result.stdout)>65536 or first.candidate.owned()!=owned:raise ValueError('Same actual candidate bounded export4 receipt required')
    value=json.loads(result.stdout)
    if (value.get('state')!='native-public-signatures-verified' or value.get('packet_sha256')!=first.digest(raw) or value.get('export_generation')!=generation or value.get('signature_attempt')!=1 or
        value.get('cleartext_equals_release') is not True or value.get('public_temporary_home_removed') is not True or set(value.get('native_verification',{}))!=set(first.native.LIMITS) or
        any(row.get('exit')!=0 for row in value['native_verification'].values()) or
        value['native_verification']['InRelease'].get('contract')!='native-gpgv-output-stdout-status-stderr-inrelease-stdin'):
        raise ValueError('Actual native export4 stream signatures/readback/cleanup required')
    fd=os.open(output,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'wb') as target:target.write(first.native.p.encoded(value));target.flush();os.fsync(target.fileno())
    first.native.sync(context)
    print(json.dumps({'state':value['state'],'receipt':str(output),'export_generation':generation,'published':False}))
if __name__=='__main__':main()

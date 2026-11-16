#!/usr/bin/env python3
"""Same verified public host packet to fixed signature3 reconciliation2 only."""
import json,os,subprocess,sys
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import stage_package_export3_signatures as first

def main():
    if sys.argv[1:]:raise SystemExit('No arbitrary path/action/signing-context arguments')
    output=first.CONTEXT/'native-signatures-verified-2.json'
    if os.path.lexists(output):raise ValueError('Preserve existing reconciliation2 receipt; no replay')
    raw=first.packet();owned=first.candidate.owned();first.candidate.bases()
    result=subprocess.run(first.candidate.ssh()+['bash /opt/toddy-build/scripts/build/phase2/image_native.sh signatures-export3-reconcile2'],
        input=raw,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=180,check=True)
    if len(result.stdout)>65536 or first.candidate.owned()!=owned:raise ValueError('Same actual candidate bounded receipt required')
    value=json.loads(result.stdout)
    if (value.get('state')!='native-public-signatures-verified' or value.get('packet_sha256')!=first.digest(raw) or value.get('reconciliation_generation')!=2 or
        value.get('previous_state')!='public-signature3-staging-intended-no-replay' or value.get('previous_attempt_claimed_success') is not False or
        value.get('cleartext_equals_release') is not True or value.get('public_temporary_home_removed') is not True or
        set(value.get('native_verification',{}))!=set(first.native.LIMITS) or any(row.get('exit')!=0 for row in value['native_verification'].values()) or
        value['native_verification']['InRelease'].get('contract')!='native-gpgv-output-stdout-status-stderr-inrelease-stdin'):
        raise ValueError('Actual linked native stream verification/cleanup required')
    fd=os.open(output,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'wb') as stream:stream.write(first.native.p.encoded(value));stream.flush();os.fsync(stream.fileno())
    first.native.sync(first.CONTEXT)
    print(json.dumps({'state':value['state'],'receipt':str(output),'reconciliation_generation':2,'published':False}))

if __name__=='__main__':main()

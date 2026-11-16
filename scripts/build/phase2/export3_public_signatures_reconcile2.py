#!/usr/bin/env python3
"""Fixed reconciliation2 of preserved failed signature3 intent; no old replay."""
import hashlib,json,os,re,subprocess,sys
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import export3_public_signatures as frozen
OLD_RECEIPT=frozen.RECEIPT;OLD_RUN=frozen.RUN
RECEIPT=Path('/var/log/toddy/phase2/package-export3-public-signatures-2.json')
RUN=frozen.TARGET/'run/toddy-export3-public-verification-2'

def previous_binding(value,raw,old):
    if (old.get('version')!=1 or old.get('state')!='public-signature3-staging-intended-no-replay' or
        old.get('packet_sha256')!=hashlib.sha256(raw).hexdigest() or old.get('private_material_transferred') is not False or
        old.get('host_verified_receipt_sha256')!=value['host_verified_receipt_sha256'] or
        old.get('host_signed_receipt_sha256')!=value['host_signed_receipt_sha256'] or
        old.get('public_input_sha256')!={'archive-export.json':value['archive_export_sha256'],'Release':value['release_sha256'],'archive-keyring.gpg':value['public_key_sha256']}):
        raise ValueError('Exact preserved failed signature3 intent and same host packet required')

def stream_verify(argv,fingerprint):
    """Actual qualified native gpgv contract: data stdout, status stderr, stdin."""
    command=list(argv);command[command.index('--status-fd')+1]='2';command[command.index('--output')+1]='-';command[-1]='-'
    data=(RUN/'InRelease').read_bytes()
    result=subprocess.run(command,input=data,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
        env={'PATH':'/usr/bin:/usr/sbin','HOME':'/root','LC_ALL':'C'},timeout=30,check=False)
    if result.returncode or len(result.stderr)>65536 or len(result.stdout)>frozen.LIMITS['InRelease']:raise ValueError('Actual native stream verification failed')
    rows=[line.split() for line in result.stderr.decode('utf-8',errors='replace').splitlines() if line.startswith('[GNUPG:] VALIDSIG ')]
    if len(rows)!=1 or rows[0][2]!=fingerprint:raise ValueError('Native stream approved fingerprint required')
    release=(frozen.EXPORT/'Release').read_bytes()
    if result.stdout!=release:raise ValueError('Actual native stdout cleartext differs from exact Release')
    frozen.write(RUN/'clear',result.stdout)
    return {'exit':0,'status_sha256':hashlib.sha256(result.stderr).hexdigest(),'cleartext_sha256':hashlib.sha256(result.stdout).hexdigest(),
        'cleartext_bytes':len(result.stdout),'contract':'native-gpgv-output-stdout-status-stderr-inrelease-stdin'}

def reconcile(raw):
    value,_=frozen.decode_packet(raw);old=frozen.p.strict(frozen.protected(OLD_RECEIPT).read_bytes());previous_binding(value,raw,old)
    if os.path.lexists(OLD_RECEIPT.with_suffix('.part')) or os.path.lexists(OLD_RUN) or any(os.path.lexists(frozen.EXPORT/name) for name in frozen.LIMITS):raise ValueError('Original temporary path or public signatures exist; reconcile outcome first')
    for name,sha in old['public_input_sha256'].items():
        if frozen.p.digest(frozen.protected(frozen.EXPORT/name))!=sha:raise ValueError('Original failed operation public source bytes changed')
    if frozen.p.digest(frozen.protected(frozen.TARGET/'usr/bin/gpgv'))!=old.get('native_gpgv_sha256'):raise ValueError('Failed intent native verifier changed')
    link={'reconciliation_generation':2,'previous_intent_sha256':frozen.p.digest(OLD_RECEIPT),
        'previous_state':'public-signature3-staging-intended-no-replay','previous_attempt_claimed_success':False,
        'reconcile_producer_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    original=(frozen.RECEIPT,frozen.RUN,frozen.verify_command,frozen.save)
    original_verify=frozen.verify_command;original_save=frozen.save
    def verify(argv,fingerprint):return stream_verify(argv,fingerprint) if '--output' in argv else original_verify(argv,fingerprint)
    def save(value):return original_save(dict(value,**link))
    frozen.RECEIPT=RECEIPT;frozen.RUN=RUN;frozen.verify_command=verify;frozen.save=save
    try:
        result=frozen.stage(raw)
        if frozen.p.digest(frozen.protected(OLD_RECEIPT))!=link['previous_intent_sha256']:raise ValueError('Original failed intent changed')
        return dict(result,**link)
    finally:frozen.RECEIPT,frozen.RUN,frozen.verify_command,frozen.save=original

def main():
    if sys.argv[1:] or os.geteuid()!=0 or Path(__file__).resolve()!=Path('/opt/toddy-build/scripts/build/phase2/export3_public_signatures_reconcile2.py'):raise ValueError('Fixed root signature3 reconciliation2 only')
    os.umask(0o077);subprocess.run(['/bin/bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
    frozen.inherited_media_lease();raw=sys.stdin.buffer.read(frozen.MAX_PACKET+1);print(json.dumps(reconcile(raw),sort_keys=True))

if __name__=='__main__':main()

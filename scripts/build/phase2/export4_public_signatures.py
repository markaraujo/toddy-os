#!/usr/bin/env python3
"""Fresh fixed export4 signatures using actually qualified native stdout contract."""
import hashlib,json,os,subprocess,sys
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import export3_public_signatures as base
import export3_public_signatures_reconcile2 as stream
EXPORT=base.TARGET/'sources/stage/toddy-package-export-4'
RECEIPT=Path('/var/log/toddy/phase2/package-export4-public-signatures-1.json')
RUN=base.TARGET/'run/toddy-export4-public-verification-1'

def stage(raw):
    # Reuse only the bounded fixed-public staging primitives. No failed export3
    # intent is consulted or repurposed, and all export3 globals are restored.
    original=(base.EXPORT,base.RECEIPT,base.RUN,base.verify_command,base.save,stream.RUN)
    verify_original=base.verify_command;save_original=base.save
    def verify(argv,fingerprint):return stream.stream_verify(argv,fingerprint) if '--output' in argv else verify_original(argv,fingerprint)
    def save(value):
        value=dict(value,export_generation=4,signature_attempt=1,producer_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
        if value.get('state')=='public-signature3-staging-intended-no-replay':value['state']='public-signature4-staging-intended-no-replay'
        return save_original(value)
    base.EXPORT=EXPORT;base.RECEIPT=RECEIPT;base.RUN=RUN;base.verify_command=verify;base.save=save;stream.RUN=RUN
    try:return dict(base.stage(raw),export_generation=4,signature_attempt=1,producer_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    finally:base.EXPORT,base.RECEIPT,base.RUN,base.verify_command,base.save,stream.RUN=original

def main():
    if sys.argv[1:] or os.geteuid()!=0 or Path(__file__).resolve()!=Path('/opt/toddy-build/scripts/build/phase2/export4_public_signatures.py'):raise ValueError('Fixed root export4 public signatures entry only')
    os.umask(0o077);subprocess.run(['/bin/bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
    base.inherited_media_lease();raw=sys.stdin.buffer.read(base.MAX_PACKET+1);print(json.dumps(stage(raw),sort_keys=True))
if __name__=='__main__':main()

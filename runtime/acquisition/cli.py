#!/usr/bin/env python3
"""Headless setup client for B03; the native settings UI consumes the same API."""
import argparse
import json
from pathlib import Path
import signal
from download import acquire, AcquisitionError
from choices import choose, hardware

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('action',choices=['plan','download'])
parser.add_argument('--mode',choices=['deferred','api','local'],default='deferred')
parser.add_argument('--cache',type=Path)
parser.add_argument('--adapter',choices=['openai-compatible','openai','anthropic','openrouter'])
parser.add_argument('--model-id')
parser.add_argument('--connection-ref')
parser.add_argument('--approve-remote',action='store_true')
parser.add_argument('--approve-network',action='store_true')
parser.add_argument('--approve-license',help='Exact displayed license identifier')
parser.add_argument('--artifact-sha256',help='Exact displayed artifact hash')
args=parser.parse_args()
try:
    lock=json.loads((Path(__file__).resolve().parents[2]/'config/phase2/local-model.lock.json').read_text())
    if args.action=='plan':
        result=choose(args.mode,model=lock,cache=args.cache,adapter_id=args.adapter,
            model_id=args.model_id,connection_ref=args.connection_ref,remote_consent=args.approve_remote,**hardware())
        if args.mode=='local':result['license_url']=lock['model']['license_url']
    else:
        if args.mode!='local' or not args.cache:
            raise AcquisitionError('local_cache_required')
        plan=choose('local',model=lock,cache=args.cache,**hardware())
        if plan['state']!='acquisition_consent_required':
            raise AcquisitionError(plan['state'])
        stopped=False
        def stop(_signum,_frame):
            global stopped
            stopped=True
        signal.signal(signal.SIGINT,stop);signal.signal(signal.SIGTERM,stop)
        result=acquire(lock['model'],args.cache,consent={'sha256':args.artifact_sha256,
            'license':args.approve_license,'network_approved':args.approve_network},canceled=lambda:stopped)
    print(json.dumps(result))
except AcquisitionError as error:
    print(json.dumps({'state':'error','code':str(error)}));raise SystemExit(1)
except (OSError,ValueError):
    print(json.dumps({'state':'error','code':'setup_io_failed'}));raise SystemExit(1)

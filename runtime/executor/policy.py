#!/usr/bin/env python3
"""Dedicated owner policy client; requires root via separate owner authentication.

No grant mutation is exported by the executor's broker-facing D-Bus interface.
The installed owner UI must invoke this fixed client through qualified polkit;
until then only a deliberate root administrator can change grants. Never import
persona/config policy or accept a grant from model output.
"""
import argparse
import json
import os
from pathlib import Path
import time
from store import Store,PolicyError


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['grant','revoke','audit'])
    parser.add_argument('--uid',type=int,required=True)
    parser.add_argument('--mode',choices=['session','standing'])
    parser.add_argument('--expires-in',type=int)
    parser.add_argument('--session')
    parser.add_argument('--state-dir',type=Path,default=Path('/var/lib/toddy/executor'))
    args=parser.parse_args()
    if os.getuid()!=0 or os.geteuid()!=0:raise SystemExit('owner_authentication_required')
    os.umask(0o077)
    try:
        store=Store(args.state_dir)
        if args.action=='grant':
            if args.expires_in is None or not 1<=args.expires_in<=365*86400:raise PolicyError('invalid_expiry')
            generation=store.set_grant(args.uid,args.mode,expires=time.time()+args.expires_in,session=args.session)
            result={'state':'granted','generation':generation,'scope':'unrestricted administration; not a reversible sandbox'}
        elif args.action=='revoke':result={'state':'revoked','generation':store.revoke(args.uid)}
        else:result={'audit':store.audit(args.uid)}
        print(json.dumps(result))
    except PolicyError as error:
        print(json.dumps({'state':'error','code':str(error)}));raise SystemExit(1)
    except (OSError,ValueError):
        print(json.dumps({'state':'error','code':'policy_io_failed'}));raise SystemExit(1)

if __name__=='__main__':main()

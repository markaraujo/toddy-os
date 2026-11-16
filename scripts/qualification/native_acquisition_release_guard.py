#!/usr/bin/python3 -I
"""Read-only final publisher/G2 native bootstrap gate; components-only is refused.

Use a verified real root tree bound read-only under a root-owned ancestor chain.
Expected public trust identities come from the publisher's independent lock, not
from this inspected root. No network, package write or signing occurs here.
"""
import argparse
import json
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from runtime.setup.pending import SetupError,_strict
from runtime.setup.releases import DIRECTORY,SOURCES,NativeCatalog,private_metadata,signature,sha


def check(root,expected_key_sha256,expected_fingerprint):
    root=Path(root)
    if not root.is_absolute() or root.is_symlink() or root.resolve()!=root or not root.is_dir():
        raise SetupError('publication_root_custody')
    if not re.fullmatch('[a-f0-9]{64}',expected_key_sha256) or not re.fullmatch('[A-F0-9]{40}|[A-F0-9]{64}',expected_fingerprint):
        raise SetupError('publication_trust_required')
    def path(virtual):
        virtual=Path(virtual)
        if not virtual.is_absolute() or '..' in virtual.parts:raise SetupError('publication_asset_path')
        return root/virtual.relative_to('/')
    def read(virtual,**options):return private_metadata(path(virtual),**options)
    def verify(keyring,detached,data):return signature(path(keyring),None if detached is None else path(detached),path(data))
    trust=_strict(read(DIRECTORY/'trust.json'))
    if trust.get('keyring_sha256')!=expected_key_sha256 or trust.get('fingerprint')!=expected_fingerprint:
        raise SetupError('publication_trust_changed')
    catalog=NativeCatalog.load(read=read,verify=verify)
    result=catalog.require_full_flow()
    return {**result,'scope':'native-bootstrap-only; other G2/ISO gates still required',
        'all_advertised_entries_full_flow':True,'expected_public_trust_matched':True}


def main():
    parser=argparse.ArgumentParser(description=__doc__,allow_abbrev=False)
    parser.add_argument('--root',required=True,type=Path)
    parser.add_argument('--expected-key-sha256',required=True)
    parser.add_argument('--expected-fingerprint',required=True)
    args=parser.parse_args()
    try:result=check(args.root,args.expected_key_sha256,args.expected_fingerprint)
    except (SetupError,OSError,ValueError):
        print(json.dumps({'state':'publication-refused','reason':'actual_full_flow_and_exact_trust_required'}));return 2
    print(json.dumps(result,sort_keys=True));return 0


if __name__=='__main__':raise SystemExit(main())

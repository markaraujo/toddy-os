#!/usr/bin/env python3
"""Classify unowned final-base files without reading private account contents."""
from collections import defaultdict
import json
import os
from pathlib import Path
import subprocess
from audit_native_elf import target_resolve

ACCOUNT_STATE={'/etc/'+name for name in ('passwd','group','shadow','gshadow','subuid','subgid','.pwd.lock','default/useradd')}
ACCOUNT_STATE|={path+'-' for path in ACCOUNT_STATE if path!='/etc/.pwd.lock'}
H08_CONFIG={'/etc/os-release','/etc/hosts','/etc/fstab','/etc/resolv.conf'}
DERIVED_STATE={'/etc/ld.so.cache':'native ldconfig','/etc/machine-id':'native systemd-machine-id-setup; first-boot regeneration still pending','/usr/share/info/dir':'native install-info shared index'}


def main():
    subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
    root=Path('/mnt/lfs');owners=defaultdict(set)
    for listing in (root/'var/lib/dpkg/info').glob('*.list'):
        for line in listing.read_text().splitlines():owners[line.rstrip('/')].add(listing.name.removesuffix('.list'))
    unknown=[];generated=[];pending=[];count=0
    for tree in ('usr','etc','lib64'):
        for base,dirs,files in os.walk(root/tree,followlinks=False):
            for name in dirs+files:
                path=Path(base)/name;virtual='/'+str(path.relative_to(root))
                if path.is_dir() and not path.is_symlink():continue
                count+=1
                if owners.get(virtual):continue
                if virtual in ACCOUNT_STATE:
                    generated.append({'path':virtual,'generator':'Shadow account/default/lock state; no contents exported'})
                elif virtual in H08_CONFIG:
                    pending.append({'path':virtual,'next_story':'H08','state':'Explicit bootstrap configuration; final identity/network/filesystem ownership pending'})
                elif virtual in DERIVED_STATE:
                    generated.append({'path':virtual,'generator':DERIVED_STATE[virtual]})
                elif virtual.startswith('/etc/systemd/system/') and path.is_symlink():
                    actual,canonical=target_resolve(root,virtual)
                    if canonical.startswith('/usr/lib/systemd/system/') and actual.is_file() and 'systemd' in owners.get(canonical,set()):
                        generated.append({'path':virtual,'generator':'Native Systemd preset/enable','owned_target':canonical})
                    else:unknown.append({'path':virtual,'problem':'Unowned or unresolved service configuration link'})
                else:unknown.append({'path':virtual,'problem':'Unclassified unowned final-base file/link'})
    print(json.dumps({'scope':'Final-base usr/etc/lib64 regular/link ownership; var/package/service data needs separate generated-state audit','files_inspected':count,'unknown':unknown,'generated_state':generated,'pending_h08_configuration':pending,'all_files_owned':not(generated or pending or unknown)},indent=2))

if __name__=='__main__':main()

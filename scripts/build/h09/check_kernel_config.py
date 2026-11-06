#!/usr/bin/env python3
"""Refuse silently dropped or changed requested kernel configuration options."""
import argparse
import hashlib
import json
from pathlib import Path
import re


def settings(path):
    values={}
    for line in path.read_text().splitlines():
        match=re.fullmatch(r'(CONFIG_[A-Z0-9_]+)=(.*)',line)
        disabled=re.fullmatch(r'# (CONFIG_[A-Z0-9_]+) is not set',line)
        if match:key,value=match.groups()
        elif disabled:key,value=disabled[1],'n'
        else:continue
        if key in values:raise ValueError('Duplicate kernel setting: '+key)
        values[key]=value
    return values


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('fragment',type=Path);parser.add_argument('resolved',type=Path)
    parser.add_argument('--source',type=Path,required=True)
    args=parser.parse_args()
    requested=settings(args.fragment);resolved=settings(args.resolved)
    declared=set()
    for path in args.source.rglob('Kconfig*'):
        if path.is_file():declared.update('CONFIG_'+name for name in re.findall(r'^\s*(?:menuconfig|config)\s+(\w+)',path.read_text(errors='strict'),re.M))
    unknown=set(requested)-declared
    if unknown:raise SystemExit('Kernel options absent from frozen source: '+str(sorted(unknown)))
    # Invisible disabled options may be omitted from .config. A requested y/m
    # value must always survive resolution explicitly; unknown names fail above.
    differences={key:{'requested':value,'resolved':resolved.get(key,'n')} for key,value in requested.items() if resolved.get(key,'n')!=value}
    if differences:raise SystemExit('Kernel settings differ: '+json.dumps(differences,sort_keys=True))
    if resolved.get('CONFIG_X86_NATIVE_CPU','n')!='n':raise SystemExit('Machine-specific kernel CPU build forbidden')
    print(json.dumps({'requested_options':len(requested),'resolved_sha256':hashlib.sha256(args.resolved.read_bytes()).hexdigest(),'configuration_only':True,'boot_validated':False}))

if __name__=='__main__':main()

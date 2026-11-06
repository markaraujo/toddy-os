#!/usr/bin/env python3
"""Read dynamic Expat API imports from installed native package payloads."""
from collections import defaultdict
import json
from pathlib import Path
import re
import subprocess


def main():
    subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
    target=Path('/mnt/lfs')
    rows=subprocess.check_output(['dpkg-query','--admindir='+str(target/'var/lib/dpkg'),'-W','-f=${Package}\t${Version}\t${Architecture}\t${Status}\n'],text=True)
    consumers=[];count=0
    for row in rows.splitlines():
        name,version,arch,status=row.split('\t')
        if status!='install ok installed':continue
        record=json.loads((Path('/var/log/toddy/packages')/f'{name}_{version}_{arch}.json').read_text())
        for virtual,entry in record['payload'].items():
            if not entry.get('sha256'):continue
            path=target/virtual.lstrip('/')
            with path.open('rb') as stream:
                if stream.read(4)!=b'\x7fELF':continue
            count+=1
            table=subprocess.check_output(['readelf','--dyn-syms','--wide',str(path)],text=True)
            imports=set()
            for line in table.splitlines():
                fields=line.split()
                if len(fields)<8 or fields[6]!='UND':continue
                symbol=fields[7].split('@')[0]
                if symbol.startswith('XML_'):imports.add(symbol)
            if imports:consumers.append({'package':name,'file':virtual,'expat_api_imports':sorted(imports)})
    print(json.dumps({'scope':'Dynamic Expat API imports only; static/bundled parsers, wrapper reachability and input bounds require separate source/runtime review','elf_files':count,'consumer_packages':sorted({r['package'] for r in consumers}),'consumers':consumers},indent=2))

if __name__=='__main__':main()

#!/usr/bin/env python3
"""Read dynamic regex imports from actual installed native package payloads."""
from collections import defaultdict
import json
from pathlib import Path
import re
import subprocess


def main():
    subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
    target=Path('/mnt/lfs')
    rows=subprocess.check_output(['dpkg-query','--admindir='+str(target/'var/lib/dpkg'),'-W','-f=${Package}\t${Version}\t${Architecture}\t${Status}\n'],text=True)
    symbols={'regcomp','regexec','regerror','regfree','re_compile_pattern','re_search','re_match','re_compile_fastmap','re_set_syntax'}
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
                if symbol in symbols:imports.add(symbol)
            if imports:consumers.append({'package':name,'file':virtual,'regex_imports':sorted(imports)})
    print(json.dumps({'scope':'Dynamic imports only; bundled/static engines require source review','elf_files':count,'consumer_packages':sorted({r['package'] for r in consumers}),'consumers':consumers},indent=2))

if __name__=='__main__':main()

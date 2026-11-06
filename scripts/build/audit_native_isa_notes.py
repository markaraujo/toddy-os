#!/usr/bin/env python3
"""Inventory ELF-declared x86 ISA requirements and actual compiler defaults."""
from collections import Counter
import json
from pathlib import Path
import re
import subprocess


def main():
    subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
    target=Path('/mnt/lfs')
    rows=subprocess.check_output(['dpkg-query','--admindir='+str(target/'var/lib/dpkg'),'-W','-f=${Package}\t${Version}\t${Architecture}\t${Status}\n'],text=True)
    results=[];count=0
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
            notes=subprocess.check_output(['chroot',str(target),'/usr/bin/readelf','--notes',virtual],text=True)
            needed=re.findall(r'x86 ISA needed: ([^\n]+)',notes)
            if needed:results.append({'package':name,'file':virtual,'declared_isa_needed':needed})
    defaults=subprocess.check_output(['chroot',str(target),'/usr/bin/env','-i','PATH=/usr/bin:/usr/sbin','LC_ALL=C',
                                      '/usr/bin/gcc','-Q','--help=target'],text=True)
    tuning={match.group(1):match.group(2) for match in re.finditer(r'^\s*(-m(?:arch|tune))=\s+(\S+)',defaults,re.M)}
    print(json.dumps({'scope':'ELF GNU ISA-needed notes and native GCC defaults; not instruction-level or alternate-CPU boot acceptance',
                      'elf_files':count,'files_without_isa_needed_notes':count-len(results),
                      'declared_requirements':dict(Counter(value for row in results for value in row['declared_isa_needed'])),
                      'compiler_defaults':tuning,'files':results,
                      'limitations':['Absent ELF notes do not prove baseline compatibility.',
                                     'Runtime-dispatched implementations need source/context review; native boot CPU matrix remains required.']},indent=2))

if __name__=='__main__':main()

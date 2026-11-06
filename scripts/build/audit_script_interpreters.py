#!/usr/bin/env python3
"""Inspect real executable shebang providers in native package payloads."""
from collections import defaultdict
import json
from pathlib import Path
import re
import shlex
import stat
import subprocess
from audit_native_elf import target_resolve


def main():
    subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
    root=Path('/mnt/lfs');owners=defaultdict(set);packages={};findings=[];scripts=[]
    output=subprocess.check_output(['dpkg-query','--admindir='+str(root/'var/lib/dpkg'),'-W','-f=${Package}\t${Version}\t${Architecture}\t${Status}\t${Depends}\n'],text=True)
    for line in output.splitlines():
        name,version,arch,status,depends=line.split('\t')
        if status!='install ok installed':continue
        record=json.loads((Path('/var/log/toddy/packages')/f'{name}_{version}_{arch}.json').read_text())
        declared=set(re.findall(r'(?:^|[,|])\s*([a-z0-9][a-z0-9+.-]*)',depends))
        packages[name]=(record,declared)
        for virtual,entry in record['payload'].items():
            if not entry.get('directory'):owners[virtual].add(name)
    for name,(record,declared) in sorted(packages.items()):
        for virtual,entry in record['payload'].items():
            if not entry.get('sha256') or not entry['mode']&0o111:continue
            path,canonical=target_resolve(root,virtual)
            with path.open('rb') as stream:first=stream.readline(4096)
            if not first.startswith(b'#!'):continue
            words=shlex.split(first[2:].decode().strip())
            if not words or not words[0].startswith('/'):
                findings.append({'package':name,'file':virtual,'problem':'Invalid shebang path'});continue
            requested=[words[0]]
            if words[0]=='/usr/bin/env':
                arguments=words[1:]
                if arguments and arguments[0]=='-S':arguments=arguments[1:]
                if not arguments or arguments[0].startswith('-') or '=' in arguments[0]:
                    findings.append({'package':name,'file':virtual,'problem':'Environment launcher needs manual review','shebang':first.decode().strip()});continue
                program=arguments[0]
                found=next((p for d in ('/usr/bin','/usr/sbin') if (p:=d+'/'+program) and target_resolve(root,p)[0].is_file()),None)
                if not found:
                    findings.append({'package':name,'file':virtual,'problem':'Environment interpreter absent','interpreter':program});continue
                requested.append(found)
            for interpreter in requested:
                actual,provider_path=target_resolve(root,interpreter)
                providers=owners.get(provider_path,set())
                scripts.append({'package':name,'file':virtual,'interpreter':interpreter,'provider_path':provider_path,'providers':sorted(providers)})
                if not actual.is_file() or not providers:
                    findings.append({'package':name,'file':virtual,'problem':'Interpreter absent or unowned','interpreter':interpreter,'provider_path':provider_path})
                elif name not in providers and not(providers&declared):
                    findings.append({'package':name,'file':virtual,'problem':'Direct interpreter provider undeclared','interpreter':interpreter,'providers':sorted(providers)})
    print(json.dumps({'scope':'Executable shebangs and env dispatch only; arbitrary dynamic tool/data/dlopen requirements remain separate','scripts':scripts,'findings':findings},indent=2))

if __name__=='__main__':main()

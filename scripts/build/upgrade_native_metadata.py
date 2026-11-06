#!/usr/bin/env python3
"""Version native package metadata from preserved, hash-verified own archives."""
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
from package_backend import PackageBackend

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
TARGET=Path('/mnt/lfs')
CACHE=Path('/var/cache/toddy/packages')
RECORDS=Path('/var/log/toddy/packages')


def digest(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def main():
    subprocess.run(['bash','-c','source "$1"; guard_target','guard',str(HERE/'target.sh')],check=True)
    backend=PackageBackend(TARGET)
    if not backend.native:raise SystemExit('Metadata closure requires accepted native Dpkg')
    plan=json.loads((ROOT/'config/native-package-metadata.json').read_text())
    additions={r['package']:r['add_depends'] for r in plan['packages']}
    output=backend.run('dpkg-query','-W','-f=${Package}\t${Version}\t${Architecture}\t${Status}\t${Depends}\n',capture_output=True,text=True).stdout
    packages={}
    for line in output.splitlines():
        name,version,arch,status,depends=line.split('\t')
        if status=='install ok installed':packages[name]=(version,arch,depends)
    destination=TARGET/'sources/evidence/h07-metadata-closure'
    destination.mkdir(parents=True,exist_ok=True)
    for name,(version,arch,depends) in sorted(packages.items()):
        if version.endswith(plan['version_suffix']):
            accepted=RECORDS/f'{name}_{version}_{arch}.json'
            row=json.loads(accepted.read_text())
            if not row['installed'] or digest(CACHE/f'{name}_{version}_{arch}.deb')!=row['archive_sha256']:
                raise SystemExit('Previously upgraded archive/record mismatch')
            continue
        archive=CACHE/f'{name}_{version}_{arch}.deb'
        record_path=RECORDS/(archive.stem+'.json')
        record=json.loads(record_path.read_text())
        if not record['installed'] or digest(archive)!=record['archive_sha256']:
            raise SystemExit('Predecessor provenance mismatch')
        conffiles=sorted(p for p,e in record['payload'].items() if p.startswith('/etc/') and e.get('sha256'))
        libtool=sorted(p for p,e in record['payload'].items() if p.startswith(('/usr/lib/','/usr/libexec/')) and p.endswith('.la') and e.get('sha256'))
        # Current target metadata must be complete and consistent even for packages
        # without new ELF edges, so create one recorded metadata generation for all.
        stage=TARGET/'sources/stage'/('metadata-'+name)
        if stage.exists():raise SystemExit('Existing metadata stage requires diagnosis: '+str(stage))
        temporary=TARGET/'sources/native-package-output'/archive.name
        temporary.parent.mkdir(mode=0o700,exist_ok=True)
        if temporary.exists() or temporary.is_symlink():raise SystemExit('Preserve existing metadata archive input')
        shutil.copy2(archive,temporary)
        try:backend.run('dpkg-deb','--raw-extract','/'+str(temporary.relative_to(TARGET)),'/'+str(stage.relative_to(TARGET)))
        finally:temporary.unlink()
        control=stage/'DEBIAN'
        if any(p.name not in {'control','md5sums','conffiles'} for p in control.iterdir()):
            raise SystemExit('Unexpected predecessor package control program/data')
        shutil.rmtree(control)
        for virtual in libtool:(stage/virtual.lstrip('/')).unlink()
        declared=set(re.findall(r'(?:^|[,|])\s*([a-z0-9][a-z0-9+.-]*)',depends))
        requirements=[]
        for provider in additions.get(name,[]):
            if provider not in packages:raise SystemExit('Missing actual provider '+provider)
            if provider not in declared:
                # Original version is the frozen ABI baseline, even if provider
                # metadata was upgraded earlier in this same deterministic loop.
                requirements.append(f'{provider} (>= {packages[provider][0].removesuffix(plan["version_suffix"])})')
        revised=', '.join(x for x in [depends,*requirements] if x)
        new_version=version+plan['version_suffix']
        command=[sys.executable,str(HERE/'stage_package.py'),name,new_version,str(stage),'--architecture',arch,
                 '--depends',revised,'--recipe',str(Path(__file__).resolve()),'--install']
        for source in record['sources']:command+=['--source',source['filename']]
        for path in conffiles:command+=['--conffile',path]
        predecessor={'package':name,'previous_version':version,'version':new_version,
                     'predecessor_archive_sha256':digest(archive),'predecessor_record_sha256':digest(record_path),
                     'removed_libtool_archives':libtool,'conffiles':conffiles,'depends':revised,'complete':False}
        result_path=destination/(name+'.json');result_path.write_text(json.dumps(predecessor,indent=2)+'\n')
        subprocess.run(command,check=True)
        actual=backend.run('dpkg-query','-W','-f=${Status}\t${Version}',name,capture_output=True,text=True).stdout
        if actual!='install ok installed\t'+new_version:raise SystemExit('Metadata upgrade postcondition failed')
        for path in libtool:
            if (TARGET/path.lstrip('/')).exists():raise SystemExit('Obsolete Libtool archive remains installed')
        predecessor['complete']=True;result_path.write_text(json.dumps(predecessor,indent=2)+'\n')
        print('Native metadata upgrade accepted:',name,new_version,flush=True)
    # Shared Info index is generated state, not the payload of one provider.
    index=TARGET/'usr/share/info/dir'
    if index.exists():index.unlink()
    for info in sorted((TARGET/'usr/share/info').rglob('*')):
        if info.is_file() and re.search(r'\.info(?:\.(?:gz|xz|bz2))?$',info.name):
            backend.run('install-info','--dir-file=/usr/share/info/dir','/'+str(info.relative_to(TARGET)))

if __name__=='__main__':main()

#!/usr/bin/env python3
"""Version native package metadata from preserved, hash-verified own archives."""
import hashlib
import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
from package_backend import PackageBackend
from perl_packlists import plan_packlist_rewrites, normalize_packlists

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
TARGET=Path('/mnt/lfs')
CACHE=Path('/var/cache/toddy/packages')
RECORDS=Path('/var/log/toddy/packages')


def digest(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def ensure_python_command_alias(stage):
    """Preserve a canonical alias when a later metadata generation is needed."""
    alias=stage/'usr/bin/python'
    if alias.is_symlink() and alias.readlink().as_posix()=='python3':
        return
    if alias.exists() or alias.is_symlink():
        raise SystemExit('Unexpected existing Python command payload')
    alias.symlink_to('python3')


EXACT_DEPENDENCY=re.compile(r'(?P<name>[a-z0-9][a-z0-9+.-]*)\s*\(\s*=\s*(?P<version>[^\s)]+)\s*\)')


def metadata_baseline(version):
    return re.sub(r'\+toddy[1-9][0-9]*$','',version)


def retarget_exact_dependencies(depends,packages):
    def replace(match):
        name=match['name']
        if name not in packages:raise ValueError('Missing exact-version provider: '+name)
        actual=packages[name][0]
        if metadata_baseline(actual)!=metadata_baseline(match['version']):
            raise ValueError('Exact dependency crosses frozen source version: '+name)
        return name+' (= '+actual+')'
    return EXACT_DEPENDENCY.sub(replace,depends)


def exact_dependency_order(packages):
    ordered=[];visiting=set();done=set()
    def visit(name):
        if name in done:return
        if name in visiting:raise ValueError('Cyclic exact-version metadata dependencies')
        if name not in packages:raise ValueError('Missing exact-version provider: '+name)
        visiting.add(name)
        for match in EXACT_DEPENDENCY.finditer(packages[name][2]):visit(match['name'])
        visiting.remove(name);done.add(name);ordered.append(name)
    for name in sorted(packages):visit(name)
    return ordered


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--only',action='append',default=[])
    args=parser.parse_args()
    subprocess.run(['bash','-c','source "$1"; guard_target','guard',str(HERE/'target.sh')],check=True)
    backend=PackageBackend(TARGET)
    if not backend.native:raise SystemExit('Metadata closure requires accepted native Dpkg')
    plan=json.loads((ROOT/'config/native-package-metadata.json').read_text())
    policy_sha256=digest(ROOT/'config/native-package-metadata.json')
    additions={r['package']:set(r['add_depends']) for r in plan['packages']}
    output=backend.run('dpkg-query','-W','-f=${Package}\t${Version}\t${Architecture}\t${Status}\t${Depends}\n',capture_output=True,text=True).stdout
    packages={}; package_states={}
    for line in output.splitlines():
        name,version,arch,status,depends=line.split('\t')
        if status not in ('install ok installed','install ok unpacked'):
            raise SystemExit('Unreviewed package state before closure: '+name+' '+status)
        packages[name]=(version,arch,depends);package_states[name]=status
    destination=TARGET/'sources/evidence/h07-metadata-closure'
    destination.mkdir(parents=True,exist_ok=True)
    # Include source-built additions accepted after the earlier 101-package
    # review, while refusing missing providers or unreviewed loader conditions.
    raw=subprocess.check_output([sys.executable,str(HERE/'audit_native_elf.py')],text=True)
    (destination/('direct-elf-before-'+hashlib.sha256(raw.encode()).hexdigest()+'.json')).write_text(raw)
    (destination/'direct-elf-before.json').write_text(raw)
    audit=json.loads(raw)
    private={'package':'systemd','file':'/usr/lib/systemd/libsystemd-core-261.so','needed':'libsystemd-shared-261.so','problem':'provider absent from reviewed native search paths'}
    for finding in audit['findings']:
        if finding['problem']=='direct native provider undeclared':
            if len(finding['providers'])!=1:raise SystemExit('Ambiguous provider requires review')
            additions.setdefault(finding['package'],set()).update(finding['providers'])
        elif finding!=private:
            raise SystemExit('Unreviewed ELF finding before metadata upgrade: '+json.dumps(finding))
    if not args.only:
        script_raw=subprocess.check_output([sys.executable,str(HERE/'audit_script_interpreters.py')],text=True)
        (destination/('script-before-'+hashlib.sha256(script_raw.encode()).hexdigest()+'.json')).write_text(script_raw)
        for finding in json.loads(script_raw)['findings']:
            if finding['problem']!='Direct interpreter provider undeclared' or len(finding['providers'])!=1:
                raise SystemExit('Unresolved script interpreter before metadata upgrade: '+json.dumps(finding))
            additions.setdefault(finding['package'],set()).update(finding['providers'])
    (destination/'derived-provider-edges.json').write_text(json.dumps({name:sorted(providers) for name,providers in sorted(additions.items())},indent=2)+'\n')
    if set(args.only)-packages.keys():raise SystemExit('Requested package is not installed')
    progress=destination/'packages';progress.mkdir(exist_ok=True)
    for name in exact_dependency_order(packages):
        version,arch,depends=packages[name]
        if args.only and name not in args.only:continue
        archive=CACHE/f'{name}_{version}_{arch}.deb'
        record_path=RECORDS/(archive.stem+'.json')
        record=json.loads(record_path.read_text())
        if digest(archive)!=record['archive_sha256']:
            raise SystemExit('Predecessor provenance mismatch')
        if not record['installed']:
            pending=json.loads((progress/(name+'.json')).read_text())
            predecessor=RECORDS/f'{name}_{pending["previous_version"]}_{arch}.json'
            if (package_states[name]!='install ok unpacked' or pending.get('complete') is not False or
                    pending['version']!=version or digest(predecessor)!=pending['predecessor_record_sha256'] or
                    not json.loads(predecessor.read_text())['installed']):
                raise SystemExit('Unreviewed partial metadata installation')
            # Recovery may use a failed own archive only if its unpacked bytes
            # still match; the failed record remains installed=False forever.
            for virtual,row in record['payload'].items():
                if row.get('directory'):continue
                path=TARGET/virtual.lstrip('/')
                if 'symlink' in row:
                    if not path.is_symlink() or path.readlink().as_posix()!=row['symlink']:raise SystemExit('Partial payload link changed')
                elif path.is_symlink() or digest(path)!=row['sha256']:raise SystemExit('Partial payload bytes changed')
        packlists=[p for p in record['payload'] if p.endswith('/.packlist')] if name.startswith('perl-') else []
        for virtual in packlists:
            if digest(TARGET/virtual.lstrip('/'))!=record['payload'][virtual]['sha256']:
                raise SystemExit('Modified installed packlist requires preservation/review')
        packlist_changes=plan_packlist_rewrites(TARGET,name,packlists,set(record['payload']))
        revision=re.search(r'\+toddy([1-9][0-9]*)$',version)
        previous_result=progress/(name+'.json')
        previous=json.loads(previous_result.read_text()) if previous_result.exists() else {}
        declared_now=set(re.findall(r'(?:^|[,|])\s*([a-z0-9][a-z0-9+.-]*)',depends))
        if revision and not packlist_changes and previous.get('complete') and previous.get('version')==version and previous.get('metadata_policy_sha256')==policy_sha256 and set(additions.get(name,[]))<=declared_now and retarget_exact_dependencies(depends,packages)==depends:
            continue
        conffiles=sorted(p for p,e in record['payload'].items() if p.startswith('/etc/') and e.get('sha256'))
        libtool=sorted(p for p,e in record['payload'].items() if p.startswith(('/usr/lib/','/usr/libexec/')) and p.endswith('.la') and e.get('sha256'))
        journal=plan.get('perl_shared_install_journal')
        shared_journals=[journal] if name.startswith('perl-') and journal in record['payload'] else []
        for virtual in shared_journals:
            if digest(TARGET/virtual.lstrip('/'))!=record['payload'][virtual]['sha256']:
                raise SystemExit('Modified shared install journal needs preservation/review')
        # Current target metadata must be complete and consistent even for packages
        # without new ELF edges, so create one recorded metadata generation for all.
        new_version=(version[:revision.start()]+'+toddy'+str(int(revision[1])+1)) if revision else version+plan['version_suffix']
        stage=TARGET/'sources/stage'/('metadata-'+name+'-'+new_version)
        if stage.exists():raise SystemExit('Existing metadata stage requires diagnosis: '+str(stage))
        temporary=backend.workspace()/archive.name
        if temporary.exists() or temporary.is_symlink():raise SystemExit('Preserve existing metadata archive input')
        shutil.copy2(archive,temporary)
        # Historic bootstrap archives carry builder account names as well as
        # numeric IDs. Native messagebus is UID 18, whereas the original builder
        # used that name for UID 101 (target tester). Preserve numeric ownership
        # so the existing reviewed policy can normalize tester, not a service UID.
        data=temporary.with_name(temporary.name+'.data.tar')
        if data.exists() or data.is_symlink():raise SystemExit('Preserve existing numeric archive input')
        try:
            with data.open('xb') as stream:
                backend.run('dpkg-deb','--fsys-tarfile','/'+str(temporary.relative_to(TARGET)),stdout=stream)
            stage.mkdir()
            backend.run('tar','--extract','--numeric-owner','--same-permissions',
                        '--file','/'+str(data.relative_to(TARGET)),
                        '--directory','/'+str(stage.relative_to(TARGET)))
            backend.run('dpkg-deb','--control','/'+str(temporary.relative_to(TARGET)),
                        '/'+str((stage/'DEBIAN').relative_to(TARGET)))
        finally:
            temporary.unlink()
            if data.exists():data.unlink()
        control=stage/'DEBIAN'
        if any(p.name not in {'control','md5sums','conffiles'} for p in control.iterdir()):
            raise SystemExit('Unexpected predecessor package control program/data')
        shutil.rmtree(control)
        if name=='python':
            ensure_python_command_alias(stage)
        for virtual in libtool+shared_journals:(stage/virtual.lstrip('/')).unlink()
        normalized_packlists=normalize_packlists(stage,name,packlists,set(record['payload']))
        declared=set(re.findall(r'(?:^|[,|])\s*([a-z0-9][a-z0-9+.-]*)',depends))
        requirements=[]
        for provider in sorted(additions.get(name,[])):
            if provider not in packages:raise SystemExit('Missing actual provider '+provider)
            if provider not in declared:
                # Original version is the frozen ABI baseline, even if provider
                # metadata was upgraded earlier in this same deterministic loop.
                baseline=re.sub(r'\+toddy[1-9][0-9]*$','',packages[provider][0])
                requirements.append(f'{provider} (>= {baseline})')
        revised=retarget_exact_dependencies(', '.join(x for x in [depends,*requirements] if x),packages)
        new_version=(version[:revision.start()]+'+toddy'+str(int(revision[1])+1)) if revision else version+plan['version_suffix']
        command=[sys.executable,str(HERE/'stage_package.py'),name,new_version,str(stage),'--architecture',arch,
                 '--depends',revised,'--recipe',str(Path(__file__).resolve()),'--install']
        for source in record['sources']:command+=['--source',source['filename']]
        for path in conffiles:command+=['--conffile',path]
        predecessor={'package':name,'previous_version':version,'version':new_version,
                     'metadata_policy_sha256':policy_sha256,
                     'predecessor_archive_sha256':digest(archive),'predecessor_record_sha256':digest(record_path),
                     'removed_libtool_archives':libtool,'removed_shared_journals':shared_journals,'normalized_perl_packlists':normalized_packlists,'conffiles':conffiles,'depends':revised,'complete':False}
        result_path=progress/(name+'.json')
        if result_path.exists():
            history=progress/'history';history.mkdir(exist_ok=True)
            preserved=history/(name+'-'+digest(result_path)+'.json')
            if not preserved.exists():shutil.copy2(result_path,preserved)
        result_path.write_text(json.dumps(predecessor,indent=2)+'\n')
        subprocess.run(command,check=True)
        actual=backend.run('dpkg-query','-W','-f=${Status}\t${Version}',name,capture_output=True,text=True).stdout
        if actual!='install ok installed\t'+new_version:raise SystemExit('Metadata upgrade postcondition failed')
        for path in libtool+shared_journals:
            if (TARGET/path.lstrip('/')).exists():raise SystemExit('Removed generated/Libtool artifact remains installed')
        predecessor['complete']=True;result_path.write_text(json.dumps(predecessor,indent=2)+'\n')
        packages[name]=(new_version,arch,revised);package_states[name]='install ok installed'
        print('Native metadata upgrade accepted:',name,new_version,flush=True)
    if args.only:return
    # Shared Info index is generated state, not the payload of one provider.
    index=TARGET/'usr/share/info/dir'
    if index.exists():index.unlink()
    for info in sorted((TARGET/'usr/share/info').rglob('*')):
        if info.is_file() and re.search(r'\.info(?:\.(?:gz|xz|bz2))?$',info.name):
            backend.run('install-info','--dir-file=/usr/share/info/dir','/'+str(info.relative_to(TARGET)))

if __name__=='__main__':main()

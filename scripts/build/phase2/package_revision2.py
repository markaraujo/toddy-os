#!/usr/bin/python3 -I
"""Frozen-primary package revision preparation; never installs, signs or publishes."""
import argparse
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import tempfile

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(ROOT),str(HERE),str(HERE.parent),str(ROOT/'scripts/qualification')]
import offline_payload as p
import archive_metadata as metadata
from package_backend import PackageBackend
from provenance import recipe_set
from run_step import snapshot as full_target_snapshot
from runtime.setup.releases import PACKAGES,POSTCONDITIONS
from runtime.installer.composition import secured

TARGET=Path('/mnt/lfs')
STAGE=TARGET/'sources/stage'
LOCK=Path('/var/log/toddy/build/build.lock')


def revision_version(old,new):
    if not isinstance(new,str) or not p.VERSION.fullmatch(new):raise ValueError('Explicit native project revision required')
    a=re.fullmatch(r'(.+\+toddy)([0-9]+)',old);b=re.fullmatch(r'(.+\+toddy)([0-9]+)',new)
    if not a or not b or a[1]!=b[1] or int(b[2])<=int(a[2]) or not p.version_satisfies(new,'>',old):raise ValueError('Only a greater project revision of the same frozen version')


def version_control(data,new):
    text=data.decode('utf-8',errors='strict');fields=p.deb822(text)
    if len({key.lower() for key in fields})!=len(fields) or '\r' in text or 'Version' not in fields:raise ValueError('Unambiguous native control required')
    revision_version(fields['Version'],new)
    lines=text.splitlines(keepends=True);found=False
    for index,line in enumerate(lines):
        if line.startswith('Version:'):
            if found or index+1<len(lines) and lines[index+1].startswith((' ','\t')):raise ValueError('Scalar native Version required')
            lines[index]='Version: '+new+'\n';found=True
    result=''.join(lines).encode()
    if not found or {key:value for key,value in p.deb822(result.decode()).items() if key!='Version'}!={key:value for key,value in fields.items() if key!='Version'}:raise ValueError('Native control fields changed')
    return result


def write(path,value):
    with Path(path).open('xb') as stream:
        os.fchmod(stream.fileno(),0o600);stream.write(p.encoded(value));stream.flush();os.fsync(stream.fileno())


def primary_provenance(component,record,archive):
    """Reuse original-source policy against exact archive-owned manifest only."""
    if component['sources']:
        if any(not p.HASH.fullmatch(source.get('sha256','')) for source in component['sources']):raise ValueError('Frozen upstream source custody missing')
        return
    virtual='/usr/share/doc/'+component['name']+'/source-manifest.json'
    with tempfile.TemporaryDirectory(prefix='toddy-revision-public-source-') as directory:
        target=Path(directory);manifest=target/virtual.lstrip('/');manifest.parent.mkdir(parents=True)
        with p.tar_stream(archive,'--fsys-tarfile') as stream:
            found=False
            for member in stream:
                if '/'+member.name.removeprefix('./').rstrip('/')!=virtual:continue
                if found or not member.isfile() or member.size>32*1024**2:raise ValueError('Bounded owned primary source manifest required')
                manifest.write_bytes(stream.extractfile(member).read());found=True
        if not found:raise ValueError('Primary source manifest missing')
        metadata.original_source_provenance(component,record,target=target)


def sync_directory(path):
    fd=os.open(path,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    try:os.fsync(fd)
    finally:os.close(fd)


def verified_built(record_path,archives):
    record_path=p.regular(record_path);record=p.strict(record_path.read_bytes())
    if record.get('name') not in PACKAGES or record.get('installed') is not False or record.get('revision_kind')!='frozen-primary-project-packaging' or record.get('packager_sha256')!=p.digest(__file__):raise ValueError('Honest current built-only revision record required')
    archive=p.regular(Path(archives)/(record_path.stem+'.deb'))
    control,body,size=p.archive_contents(archive)
    if control.get('Package')!=record['name'] or control.get('Version')!=record['version'] or p.digest(archive)!=record['archive_sha256'] or body!=record['payload']:raise ValueError('Built-only revision archive/record differs')
    revision_version(record['primary_version'],record['version'])
    primary_stem=record['name']+'_'+record['primary_version']+'_'+control['Architecture']
    primary_record=p.regular(Path(archives)/(primary_stem+'.json'))
    original=p.component_from_record(primary_record,archives)
    old=p.regular(Path(archives)/(primary_stem+'.deb'));old_control,old_body,_=p.archive_contents(old)
    primary_provenance(original,p.strict(primary_record.read_bytes()),old)
    if p.digest(primary_record)!=record['primary_record_sha256'] or p.digest(old)!=record['primary_archive_sha256'] or old_body!=body or record['sources']!=p.strict(primary_record.read_bytes())['sources'] or {key:value for key,value in control.items() if key!='Version'}!={key:value for key,value in old_control.items() if key!='Version'}:
        raise ValueError('Revision frozen primary provenance/control/payload differs')
    return record,archive,control,body,size


@contextmanager
def build_guard():
    if os.getuid()!=0 or os.geteuid()!=0 or Path(__file__).resolve()!=Path('/opt/toddy-build/scripts/build/phase2/package_revision2.py'):raise ValueError('Designated native builder only')
    subprocess.run(['/bin/bash','-c','source "$1"; guard_target','guard',str(HERE.parent/'target.sh')],check=True)
    if (LOCK.parent/'input-sync.running').exists():raise ValueError('Build input synchronization unfinished')
    fd=os.open(LOCK,os.O_RDWR|os.O_NOFOLLOW|os.O_CLOEXEC)
    try:
        info=os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_uid!=0 or info.st_mode&0o022:raise ValueError('Existing build lock custody')
        fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB);yield
    finally:os.close(fd)


def prepare(primary_record,archives,new_version):
    """Actual native archive build when parent executes; target packages untouched."""
    with build_guard():
        primary_record=secured(primary_record,32*1024**2)
        original=p.component_from_record(primary_record,archives)
        if original['name'] not in PACKAGES:raise ValueError('Only curated acquisition package revision')
        revision_version(original['version'],new_version)
        raw=p.strict(primary_record.read_bytes());old=secured(Path(archives)/(primary_record.stem+'.deb'),2*1024**3)
        control,body,installed_bytes=p.archive_contents(old)
        primary_provenance(original,raw,old)
        backend=PackageBackend(TARGET)
        if not backend.native:raise ValueError('No bootstrap/host archive producer fallback')
        work=STAGE/('acquisition-revision-'+original['name']+'-'+new_version)
        if work.resolve()!=work or os.path.lexists(work):raise ValueError('Preserve old/uncertain revision generation')
        if shutil.disk_usage(STAGE).free<metadata.NATIVE_RESERVE+2*installed_bytes+4*old.stat().st_size+8*1024**2:raise ValueError('Revision preparation native capacity')
        before=p.digest(TARGET/'var/lib/dpkg/status');projection_before=full_target_snapshot();work.mkdir(mode=0o700)
        source=work/old.name;shutil.copyfile(old,source);source.chmod(0o600)
        shutil.copyfile(primary_record,work/primary_record.name);(work/primary_record.name).chmod(0o600)
        if p.digest(source)!=original['archive_sha256']:raise ValueError('Frozen primary copy differs')
        stage=work/'payload'
        backend.run('dpkg-deb','--raw-extract','/'+source.relative_to(TARGET).as_posix(),'/'+stage.relative_to(TARGET).as_posix())
        file=stage/'DEBIAN/control';before_control=file.read_bytes();updated=version_control(before_control,new_version)
        file.write_bytes(updated)
        stem=original['name']+'_'+new_version+'_'+original['architecture'];archive=work/(stem+'.deb')
        backend.build(stage,archive,threads=8)
        final_control,final_body,_=p.archive_contents(archive)
        if final_body!=body or {key:value for key,value in final_control.items() if key!='Version'}!={key:value for key,value in control.items() if key!='Version'} or final_control.get('Version')!=new_version or p.digest(TARGET/'var/lib/dpkg/status')!=before:raise ValueError('Revision changed frozen payload/control/target state')
        projection_after=full_target_snapshot()
        if projection_after!=projection_before:raise ValueError('Unqualified native archive build changed target projection')
        projection_sha=hashlib.sha256(p.encoded(projection_before)).hexdigest()
        record={**raw,'version':new_version,'archive_sha256':p.digest(archive),'recipe_sha256':p.digest(__file__),
            'packager_sha256':p.digest(__file__),'supporting_build_scripts':recipe_set(),'packaging_backend':backend.record,
            'installed':False,'revision_kind':'frozen-primary-project-packaging','primary_version':original['version'],
            'primary_archive_sha256':original['archive_sha256'],'primary_record_sha256':original['component_record_sha256'],
            'native_target_dpkg_before':before,'native_target_dpkg_after':p.digest(TARGET/'var/lib/dpkg/status'),
            'payload_unchanged':True,'control_changed_fields':['Version'],'full_root_verification':{'before_sha256':projection_sha,'after_sha256':hashlib.sha256(p.encoded(projection_after)).hexdigest(),'changed_paths':0,'optimized_build_isolation_qualified':False}}
        for durable in (source,work/primary_record.name,archive):
            with durable.open('rb') as stream:os.fsync(stream.fileno())
        write(work/(stem+'.json'),record)
        write(work/'prepared.json',{'version':1,'state':'native-archive-built-not-installed','package':original['name'],
            'package_version':new_version,'archive_sha256':record['archive_sha256'],'record_sha256':p.digest(work/(stem+'.json')),
            'primary':original,'installed':False,'signed':False,'runtime_qualified':False})
        sync_directory(work)
        return {'state':'native-archive-built-not-installed','work':str(work),'installed':False,'signed':False}


def export_metadata(record_path,archives,output,issued,expires,scope):
    """Public unsigned APT is allowed before installation; no circular proof."""
    record,archive,control,body,size=verified_built(record_path,archives);trust=metadata.public_trust()
    component={'name':record['name'],'version':record['version'],'architecture':control['Architecture'],
        'depends':control.get('Depends',''),'archive_sha256':record['archive_sha256'],'component_record_sha256':p.digest(record_path),
        'recipe_sha256':record['recipe_sha256'],'sources':[{('public_verification_material_sha256' if key=='key_sha256' else key):value for key,value in source.items()} for source in record['sources']],
        'copyright':{'path':'/usr/share/doc/'+record['name']+'/copyright','sha256':body['/usr/share/doc/'+record['name']+'/copyright']['sha256']},
        'source_notices_index':None}
    index='/usr/share/doc/'+record['name']+'/source-notices/index.json'
    if index in body:component['source_notices_index']={'path':index,'sha256':body[index]['sha256']}
    legal,names=metadata.legal_assets(archive,component)
    item={'component':component,'control':control,'payload':{path:body[path] for path,owner in POSTCONDITIONS.items() if owner==record['name']},
        'installed_bytes':size,'archive':archive,'record':record_path,'asset':record['name']+'_'+record['archive_sha256']+'.deb',
        'legal_data':legal,'legal_assets':names}
    files,inventory=metadata.documents({record['name']:item},trust,issued,expires)
    output=Path(output)
    if not output.is_absolute() or output.resolve()!=output or os.path.lexists(output) or not output.parent.is_dir():raise ValueError('New revision metadata output required')
    reserve=metadata.reserve_for(output,scope)
    if shutil.disk_usage(output.parent).free<reserve+archive.stat().st_size+sum(map(len,files.values()))+8*1024**2:raise ValueError('Revision public metadata capacity')
    output.mkdir(mode=0o700);hashes={}
    for name,data in files.items():
        with (output/name).open('xb') as stream:os.fchmod(stream.fileno(),0o644);stream.write(data);stream.flush();os.fsync(stream.fileno())
        hashes[name]=p.digest(output/name)
    destination=output/item['asset']
    with archive.open('rb') as source,destination.open('xb') as stream:
        os.fchmod(stream.fileno(),0o644);shutil.copyfileobj(source,stream,1024*1024);stream.flush();os.fsync(stream.fileno())
    if p.digest(destination)!=record['archive_sha256']:raise ValueError('Revision public archive copy differs')
    hashes[item['asset']]=p.digest(destination)
    result={'version':1,'kind':'unsigned-native-revision-built-only-export','files':hashes,'package':inventory[0],
        'built_record_sha256':p.digest(record_path),'primary_record_sha256':record['primary_record_sha256'],
        'public_fingerprint':trust['fingerprint'],'installed':False,'signed':False,'runtime_qualified':False}
    write(output/'revision2-export.json',result);sync_directory(output)
    return {'state':result['kind'],'installed':False,'signed':False}


def installed_record(record_path,archives,output):
    """New truthful installed record only after real parent-owned native upgrade."""
    from native_acquisition_full_flow import guard
    guard();record,archive,control,body,size=verified_built(record_path,archives);name=record['name']
    target=Path(output)
    if target.parent!=Path('/var/lib/toddy/native-acquisition-full-flow-1/lifecycle-artifact2') or target.name!=Path(record_path).name or os.path.lexists(target):raise ValueError('New fixed lifecycle installed record required')
    result=subprocess.check_output(['/usr/bin/dpkg-query','-W','-f=${Status}\t${Version}\t${Architecture}',name],text=True)
    if result!='install ok installed\t'+record['version']+'\t'+control['Architecture']:raise ValueError('Actual installed revision2 missing')
    before=p.digest(Path('/var/lib/dpkg/status'));checked=0
    for virtual,row in body.items():
        path=Path(virtual);info=path.lstat()
        if path.parent.resolve()!=path.parent or (info.st_mode,info.st_uid,info.st_gid)!=(row['mode'],row['uid'],row['gid']):raise ValueError('Actual installed revision metadata differs')
        if 'sha256' in row:
            if not stat.S_ISREG(info.st_mode) or p.digest(path)!=row['sha256']:raise ValueError('Actual installed frozen bytes differ')
        elif 'symlink' in row:
            if not path.is_symlink() or os.readlink(path)!=row['symlink']:raise ValueError('Actual installed revision link differs')
        elif not stat.S_ISDIR(info.st_mode):raise ValueError('Actual installed revision directory differs')
        if not row.get('directory'):
            owner=subprocess.check_output(['/usr/bin/dpkg-query','-S',virtual],text=True).strip()
            if owner!=name+': '+virtual:raise ValueError('Actual installed native ownership differs')
        checked+=1
    audit=subprocess.run(['/usr/bin/dpkg','--audit'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    if audit.returncode or audit.stdout or audit.stderr or p.digest(Path('/var/lib/dpkg/status'))!=before:raise ValueError('Actual package audit/state not stable')
    observed={**record,'installed':True,'native_revision_postcheck':{'producer_sha256':p.digest(__file__),
        'built_record_sha256':p.digest(record_path),'archive_sha256':p.digest(archive),'checked_entries':checked,
        'actual_inventory':{'name':name,'version':record['version'],'architecture':control['Architecture']},
        'native_dpkg_status_sha256':before,'native_audit_exit':0,'package_operation_executed_by_this_script':False}}
    write(target,observed);sync_directory(target.parent)
    return {'state':'actual-installed-revision2-recorded','checked_entries':checked,'record_sha256':p.digest(target),'runtime_qualified':False}


def main():
    parser=argparse.ArgumentParser(description=__doc__,allow_abbrev=False);commands=parser.add_subparsers(dest='action',required=True)
    build=commands.add_parser('prepare');build.add_argument('--primary-record',type=Path,required=True);build.add_argument('--archives',type=Path,default=Path('/var/cache/toddy/packages'));build.add_argument('--version',required=True)
    meta=commands.add_parser('metadata');meta.add_argument('--record',type=Path,required=True);meta.add_argument('--archives',type=Path,required=True);meta.add_argument('--output',type=Path,required=True);meta.add_argument('--issued-unix',type=int,required=True);meta.add_argument('--expires-unix',type=int,required=True);meta.add_argument('--capacity-scope',choices=('host-export','native-target'),required=True)
    observe=commands.add_parser('observe-installed');observe.add_argument('--record',type=Path,required=True);observe.add_argument('--archives',type=Path,required=True);observe.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.action=='prepare':result=prepare(args.primary_record,args.archives,args.version)
    elif args.action=='metadata':result=export_metadata(args.record,args.archives,args.output,args.issued_unix,args.expires_unix,args.capacity_scope)
    else:result=installed_record(args.record,args.archives,args.output)
    print(p.encoded(result).decode(),end='')


if __name__=='__main__':main()

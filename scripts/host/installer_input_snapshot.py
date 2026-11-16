#!/usr/bin/env python3
"""Build an explicit read-only qualification-input ISO; no native disk writes."""
import argparse,hashlib,json,os,re,shutil,stat,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts/build/phase2')]
import offline_payload as p
from runtime.installer.composition import SOURCES,source_path,bundle_namespace,validate_policy,validate_installed_handoff
from runtime.installer.installed_boot import InstalledBoot

CONTEXT=ROOT/'.local/phase2/native-installer-1'
HELPERS=('scripts/build/phase2/installer_qualification.py','scripts/build/phase2/installer_collect.py',
         'scripts/build/h10/root_inventory.py','scripts/host/installer-live-probe.py')
FLOOR=100*1024**3+512*1024**2


def regular(path):
    path=p.regular(Path(path));info=path.stat()
    if path.resolve()!=path or info.st_nlink!=1:raise ValueError('Canonical independent snapshot file required')
    return path


def selected_files(native,repository):
    native=Path(native);repository=Path(repository)
    manifest_path=regular(native/'payload/manifest.json')
    prepared=p.PreparedPayload(native/'payload',manifest_sha256=p.digest(manifest_path),runner=None,finalizer=None)
    manifest=prepared._load();bundle_namespace(native/'payload',manifest)
    files={}
    for base,dirs,leaves in os.walk(native/'payload',followlinks=False):
        for name in dirs:
            path=Path(base)/name
            if path.resolve()!=path:raise ValueError('No redirected snapshot payload directory')
        for name in leaves:
            path=regular(Path(base)/name);files['inputs/'+path.relative_to(native).as_posix()]=path
    for name in ('policy.json','boot-profile.json','generated-entries.json','expected-image-manifest.json'):files['inputs/'+name]=regular(native/name)
    policy=p.strict(files['inputs/policy.json'].read_bytes());validate_policy(policy,manifest)
    boot=p.strict(files['inputs/boot-profile.json'].read_bytes());InstalledBoot(native/'payload',manifest,boot,None)
    storage=manifest.get('storage',{})
    if storage.get('version')!=1 or storage.get('block_bytes')!=4096 or storage.get('logical_regular_path_bytes')!=manifest['bytes'] or type(storage.get('root_storage_bound_bytes')) is not int or storage['root_storage_bound_bytes']<manifest['bytes']:raise ValueError('Actual prepared native storage measurements required')
    source_hashes={}
    for name in SOURCES:
        current=source_path(name);relative=current.relative_to(ROOT).as_posix();path=regular(repository/relative)
        files['source/'+relative]=path;source_hashes[name]=p.digest(path)
    validate_installed_handoff(manifest,source_hashes)
    for relative in HELPERS:files['source/'+relative]=regular(repository/relative)
    descriptor={'payload_manifest_sha256':p.digest(manifest_path),'policy_sha256':p.digest(files['inputs/policy.json']),
        'image_manifest_sha256':hashlib.sha256(p.encoded(p.strict(files['inputs/expected-image-manifest.json'].read_bytes()))).hexdigest()}
    return files,descriptor


def installed_sources(record_paths,archives,files):
    payloads={};manifests={}
    for record_path in record_paths:
        component=p.component_from_record(record_path,archives);name=component['name']
        if name not in ('toddy-installer','toddy-assistant') or name in manifests:raise ValueError('Exact installer/assistant native source records required')
        record=p.strict(regular(record_path).read_bytes());payloads.update(record['payload'])
        manifests[name]=record['payload']['/usr/share/doc/'+name+'/source-manifest.json']['sha256']
    if set(manifests)!={'toddy-installer','toddy-assistant'}:raise ValueError('Both installed source manifest pins required')
    mapping={}
    for name in SOURCES:
        relative=source_path(name).relative_to(ROOT).as_posix()
        target='/usr/lib/toddy/'+name if name.startswith(('setup/','shared/')) else '/usr/lib/toddy/installer/'+name
        digest=p.digest(files['source/'+relative])
        if payloads.get(target,{}).get('sha256')!=digest:raise ValueError('Frozen installed runtime source differs: '+name)
        mapping[relative]=target
    return mapping,manifests


def create(native,repository,commit,record_paths,archives,xorriso):
    if os.getuid()==0 or os.geteuid()==0:raise ValueError('Use the nonroot owner source-custody controller')
    repository=Path(repository)
    if repository.resolve()!=repository or repository!=ROOT:raise ValueError('Exact reviewed checkout required')
    if not re.fullmatch('[a-f0-9]{40}',commit):raise ValueError('Explicit full reviewed source commit required')
    if subprocess.check_output(['git','rev-parse',commit+'^{commit}'],cwd=ROOT,text=True).strip()!=commit:raise ValueError('Actual full source commit required')
    if subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip():raise ValueError('Commit qualification source inputs first')
    files,descriptor=selected_files(native,repository);runtime,manifests=installed_sources(record_paths,archives,files)
    for path in (path for name,path in files.items() if name.startswith('source/')):
        relative=path.relative_to(ROOT).as_posix()
        if subprocess.check_output(['git','show',commit+':'+relative],cwd=ROOT)!=path.read_bytes():raise ValueError('Snapshot source differs from exact reviewed commit')
    xorriso=regular(xorriso)
    environment={'PATH':'/usr/bin:/usr/sbin','HOME':'/nonexistent','LC_ALL':'C','TZ':'UTC','SOURCE_DATE_EPOCH':'1794009600'}
    version=subprocess.check_output([str(xorriso),'-no_rc','-version'],stderr=subprocess.STDOUT,text=True,timeout=10,env=environment)
    value={'version':1,'kind':'native-installer-qualification-snapshot-v1','source_commit':commit,
        'files':{name:p.digest(path) for name,path in sorted(files.items())},'descriptor':descriptor,
        'payload_storage':p.strict(files['inputs/payload/manifest.json'].read_bytes()).get('storage'),
        'installed_runtime':runtime,'installed_manifests':manifests,
        'runtime_source_sha256':{name:p.digest(files['source/'+source_path(name).relative_to(ROOT).as_posix()]) for name in SOURCES},
        'expected_kernel_sha256':p.strict(files['inputs/boot-profile.json'].read_bytes())['kernel_sha256'],'runtime_acceptance':False,
        'producer_sha256':p.digest(__file__),'xorriso_sha256':p.digest(xorriso),'xorriso_version':version}
    extra=sum(path.stat().st_size+4096 for path in files.values())+128*1024**2
    if shutil.disk_usage(ROOT).free<FLOOR+extra:raise ValueError('Snapshot100GiB reserve plus output headroom required')
    if CONTEXT.exists():
        info=CONTEXT.lstat()
        if CONTEXT.resolve()!=CONTEXT or info.st_uid!=os.getuid() or stat.S_IMODE(info.st_mode)!=0o700 or list(CONTEXT.iterdir()):raise ValueError('New empty private installer context required')
    else:CONTEXT.mkdir(mode=0o700)
    output=CONTEXT/'qualification-inputs';output.mkdir(mode=0o700)
    descriptor_path=output/'snapshot.json'
    with descriptor_path.open('xb') as stream:os.fchmod(stream.fileno(),0o600);stream.write(p.encoded(value));stream.flush();os.fsync(stream.fileno())
    arguments=[str(xorriso),'-no_rc','-as','mkisofs','-R','-file-mode','0444','-dir-mode','0555','-iso-level','3','--modification-date=2026110700000000','--set_all_file_dates','2026.11.07.000000','-uid','0','-gid','0','-V','TODDY_INSTALL_INPUTS','-o',str(output/'inputs.iso'),'-graft-points','snapshot.json='+str(descriptor_path)]
    arguments.extend(name+'='+str(path) for name,path in sorted(files.items()))
    with (output/'xorriso.log').open('xb') as log:subprocess.run(arguments,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=600,env=environment)
    for name,path in files.items():
        if p.digest(path)!=value['files'][name]:raise ValueError('Snapshot input changed during ISO construction')
    iso=regular(output/'inputs.iso');iso.chmod(0o600)
    result={'version':1,'state':'qualification-snapshot-created-not-booted','snapshot_sha256':p.digest(descriptor_path),'iso_sha256':p.digest(iso),'iso_bytes':iso.stat().st_size,'source_commit':commit,'production_ready':False}
    with (output/'complete.json').open('xb') as stream:os.fchmod(stream.fileno(),0o600);stream.write(p.encoded(result));stream.flush();os.fsync(stream.fileno())
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__,allow_abbrev=False)
    parser.add_argument('--native-inputs',required=True,type=Path);parser.add_argument('--source-commit',required=True)
    parser.add_argument('--record',required=True,type=Path,action='append');parser.add_argument('--archives',required=True,type=Path)
    parser.add_argument('--xorriso',type=Path,default=Path('/usr/bin/xorriso'))
    args=parser.parse_args();print(p.encoded(create(args.native_inputs,ROOT,args.source_commit,args.record,args.archives,args.xorriso)).decode(),end='')


if __name__=='__main__':main()

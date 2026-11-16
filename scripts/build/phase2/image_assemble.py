"""Fixed source-only first native archive assembly; never production readiness.

Run inside the coordinator's guarded native target chroot, under its build lock.
No disks are partitioned, existing roots resumed, or production gates bypassed.
The resulting root is a candidate for independent generated-resource review.
"""
import fcntl
import json
import os
from pathlib import Path
import stat
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT), str(Path(__file__).resolve().parent)]
from runtime.installer.composition import bundle_namespace, secured
from runtime.installer.linux_disk import LinuxDisk
from runtime.installer.native_finalizer import payload_module

STAGE = Path('/sources/stage')
GENERATIONS = {'base': ('toddy-offline-image-1', 'toddy-installer-native-inputs'),
               'live': ('toddy-live-image-1', 'toddy-live-native-inputs'),
               'base-reviewed': ('toddy-offline-image-2', 'toddy-installer-native-inputs'),
               'live-reviewed': ('toddy-live-image-2', 'toddy-live-native-inputs'),
               'mvp-base': ('toddy-mvp-offline-image-1','toddy-mvp-installer-native-inputs'),
               'mvp-live': ('toddy-mvp-live-image-1','toddy-mvp-live-native-inputs'),
               'mvp-base-reviewed': ('toddy-mvp-offline-image-2','toddy-mvp-installer-native-inputs'),
               'mvp-live-reviewed': ('toddy-mvp-live-image-2','toddy-mvp-live-native-inputs')}
MVP_CLASS='phase2-mvp-preinstalled-v1'

def check_delivery_kind(kind,manifest):
    mvp=kind.startswith('mvp-')
    if mvp!=(manifest.get('delivery_class')==MVP_CLASS) or (mvp and manifest.get('g2_eligible') is not False):
        raise ValueError('Image slot and typed delivery class differ')

def reviewed_root_name(kind):
    return ('mvp-' if kind.startswith('mvp-') else '')+('offline-root-2' if kind.removeprefix('mvp-').startswith('base') else 'live-root-2')
RESERVE = 16 * 1024**3


def private_directory(path, mode):
    path = Path(path)
    info = path.lstat()
    if (path.resolve() != path or not stat.S_ISDIR(info.st_mode) or info.st_uid or
            info.st_gid or stat.S_IMODE(info.st_mode) != mode):
        raise ValueError('Native assembly directory custody')
    return info


def native_guard(system):
    system.require_root()
    node = Path('/dev/vdb4').stat()
    if not stat.S_ISBLK(node.st_mode) or Path('/').stat().st_dev != node.st_rdev:
        raise ValueError('Assembly requires designated native target root, not builder/host root')
    if system.run(['/usr/bin/lsblk', '-dn', '-o', 'SERIAL', '/dev/vdb']) != 'TODDY-LFS-TARGET':
        raise ValueError('Assembly target serial')
    if system.run(['/usr/sbin/blkid', '-s', 'LABEL', '-o', 'value', '/dev/vdb4']) != 'TODDY_LFS':
        raise ValueError('Assembly target label')


def write(path, value):
    p = payload_module()
    with Path(path).open('xb') as stream:
        os.fchmod(stream.fileno(), 0o600)
        stream.write(p.encoded(value)); stream.flush(); os.fsync(stream.fileno())


def policy_input(base,manifest):
    """Raw-file and canonical policy identities must agree before native writes."""
    from runtime.installer.composition import validate_policy
    p=payload_module();path=secured(Path(base)/'policy.json');data=path.read_bytes();policy=p.strict(data)
    validate_policy(policy,manifest)
    if data!=p.encoded(policy):
        raise ValueError('Reviewed policy.json must use canonical payload JSON encoding')
    return policy


def root_storage_budget(kind,manifest,block):
    p=payload_module();storage=manifest.get('storage',{})
    if (type(storage.get('version')) is not int or storage.get('version')!=1 or storage.get('block_bytes')!=block or
            type(storage.get('root_storage_bound_bytes')) is not int or storage['root_storage_bound_bytes']<=0 or
            storage.get('logical_regular_path_bytes')!=manifest.get('bytes')):
        raise ValueError('Verified archive storage measurements required before image allocation')
    base=STAGE/GENERATIONS[kind][1]
    policy=policy_input(base,manifest)
    from runtime.installer.native_finalizer import account_files
    accounts=p.file_tree_storage_bound({name:len(data) for name,(data,_) in account_files(policy['accounts']).items()},block)
    embedded=0
    if kind.removeprefix('mvp-').startswith('live'):
        # Reserve the actual offline base inputs required by a production live
        # image, even while the first source-only image awaits real boot seals.
        base_kind='mvp-base' if kind.startswith('mvp-') else 'base'
        bundle=STAGE/GENERATIONS[base_kind][1]/'payload'
        sha=p.digest(secured(bundle/'manifest.json'))
        prepared=p.PreparedPayload(bundle,manifest_sha256=sha,runner=None,finalizer=None)._load()
        bundle_namespace(bundle,prepared)
        files={'usr/share/toddy/installer/composition/payload/'+path.relative_to(bundle).as_posix():secured(path,limit=8*1024**3).stat().st_size
               for path in bundle.rglob('*') if path.is_file()}
        for name in ('policy.json','generated-entries.json','expected-image-manifest.json','boot-profile.json'):
            path=bundle.parent/name
            if path.exists():files['usr/share/toddy/installer/composition/'+name]=secured(path).stat().st_size
        embedded=p.file_tree_storage_bound(files,block)
    return {'version':1,'block_bytes':block,'archive_root_bound_bytes':storage['root_storage_bound_bytes'],
        'fresh_account_bound_bytes':accounts,'embedded_offline_input_bound_bytes':embedded,
        'root_bound_bytes':storage['root_storage_bound_bytes']+accounts+embedded,
        'fixed_filesystem_and_generated_headroom_bytes':512*1024**2,
        'embedded_inputs_reserved_not_installed':bool(embedded),
        'future_qualification_artifacts_require_separate_pre_copy_measurement':bool(embedded)}


class AssemblyRoot:
    """One fixed, new same-filesystem generation; inode-pinned across commands."""
    def __init__(self, kind, manifest):
        if kind not in GENERATIONS:
            raise ValueError('Unknown fixed image profile')
        check_delivery_kind(kind,manifest)
        self.work = STAGE/GENERATIONS[kind][0]
        self.root = self.work/(reviewed_root_name(kind) if kind.endswith('-reviewed') else 'root')
        parent = STAGE.lstat()
        if (STAGE.resolve() != STAGE or not stat.S_ISDIR(parent.st_mode) or parent.st_uid or
                parent.st_gid or parent.st_mode & 0o022 or parent.st_dev != Path('/').stat().st_dev):
            raise ValueError('Native assembly stage custody')
        if os.path.lexists(self.work):
            raise ValueError('Preserve existing/uncertain native assembly generation')
        self.storage_budget=root_storage_budget(kind,manifest,os.statvfs(STAGE).f_frsize)
        # Keep the existing three-copy envelope and fixed margin. Replace only
        # its underestimated logical byte input with measured allocation bounds.
        self.required = RESERVE + 3*self.storage_budget['root_bound_bytes'] + self.storage_budget['fixed_filesystem_and_generated_headroom_bytes']
        space = os.statvfs(STAGE)
        if space.f_bavail*space.f_frsize < self.required:
            raise ValueError('Native assembly capacity requires16GiB plus3xpayload plus512MiB')
        self.work.mkdir(mode=0o700); self.root.mkdir(mode=0o755)
        # Match the explicit empty ext4 directory expected in installed roots.
        # This stages declared bytes/metadata; it is not a filesystem proof.
        (self.root/'lost+found').mkdir(mode=0o700)
        self.pin = self.identity()

    def identity(self):
        work = private_directory(self.work, 0o700)
        root = private_directory(self.root, 0o755)
        if root.st_dev != work.st_dev or root.st_dev != STAGE.stat().st_dev or os.path.ismount(self.root):
            raise ValueError('Native assembly redirected/cross-device root')
        return (work.st_dev, work.st_ino, root.st_ino)

    def recheck(self):
        if self.identity() != self.pin:
            raise ValueError('Native assembly root identity changed')


def unpack_native(bundle, manifest_sha256, assembly, system):
    """Actual fixed native Dpkg only; produces an explicitly unqualified root.

    A production PreparedPayload target guard is never changed. This developer
    component has its own fixed private stage/inode guard and no disk-plan API.
    """
    p = payload_module(); bundle = Path(bundle)
    prepared = p.PreparedPayload(bundle, manifest_sha256=manifest_sha256,
        runner=None, finalizer=None)
    manifest = prepared._load(); bundle_namespace(bundle, manifest)
    system.require_root(); assembly.recheck()
    for entry in assembly.root.iterdir():
        info=entry.lstat()
        if (entry.name!='lost+found' or not stat.S_ISDIR(info.st_mode) or info.st_uid or info.st_gid or
                stat.S_IMODE(info.st_mode)!=0o700 or list(entry.iterdir())):
            raise ValueError('Native assembly root must be fresh; never replay unpack')
    for name in ('dpkg', 'dpkg-query'):
        virtual = '/usr/bin/'+name
        if p.digest(secured(virtual)) != manifest['ownership']['entries'][virtual]['sha256']:
            raise ValueError('Native package tool differs from selected source-owned closure')
    archives = [str(bundle/'archives'/row['archive']) for row in manifest['components']]
    intent = {'version':1, 'state':'unpack-intended', 'kind':'candidate-unqualified-root',
        'manifest_sha256':manifest_sha256, 'root':str(assembly.root),
        'required_bytes':assembly.required, 'storage_budget':assembly.storage_budget, 'assembly_pin':list(assembly.pin), 'production_ready':False,
        'native_boot_verified':False}
    write(assembly.work/'unpack-intent.json', intent)
    log = '--log='+str(assembly.work/'dpkg.log')
    system.run(['/usr/bin/dpkg', '--root='+str(assembly.root), log, '--unpack', *archives], timeout=1800)
    assembly.recheck()
    system.run(['/usr/bin/dpkg', '--root='+str(assembly.root), log, '--configure', '--pending'], timeout=900)
    assembly.recheck()
    observed = system.run(['/usr/bin/dpkg-query', '--admindir='+str(assembly.root/'var/lib/dpkg'),
        '-W', '-f=${Package}\t${Version}\t${Architecture}\t${Status}\n'])
    rows = [line.split('\t') for line in observed.splitlines()]
    expected = sorted([row['name'],row['version'],row['architecture'],'install ok installed'] for row in manifest['components'])
    if sorted(rows) != expected or system.run(['/usr/bin/dpkg', '--root='+str(assembly.root), log, '--audit']):
        raise ValueError('Native assembly database is not exact/configured')
    if prepared._load() != manifest:
        raise ValueError('Native assembly input changed')
    assembly.recheck()
    result = {**intent, 'state':'native-archives-unpacked-needs-resource-qualification',
        'configured_packages':len(rows), 'dpkg_log_sha256':p.digest(assembly.work/'dpkg.log')}
    write(assembly.work/'unpacked.json', result)
    return result


def adopt_unpacked(kind, manifest, manifest_sha256, system):
    """Continue read-only custody of a completed unpack, never replay its writes."""
    if kind not in GENERATIONS:
        raise ValueError('Unknown fixed image profile')
    p=payload_module();assembly=object.__new__(AssemblyRoot)
    assembly.work=STAGE/GENERATIONS[kind][0];assembly.root=assembly.work/'root'
    intent=p.strict(secured(assembly.work/'unpack-intent.json').read_bytes())
    result=p.strict(secured(assembly.work/'unpacked.json').read_bytes())
    if (intent.get('manifest_sha256')!=manifest_sha256 or result.get('manifest_sha256')!=manifest_sha256 or
            intent.get('root')!=str(assembly.root) or result.get('root')!=str(assembly.root) or
            intent.get('state')!='unpack-intended' or result.get('state')!='native-archives-unpacked-needs-resource-qualification' or
            intent.get('assembly_pin')!=result.get('assembly_pin') or intent.get('required_bytes')!=result.get('required_bytes') or
            type(intent.get('required_bytes')) is not int or intent['required_bytes']<=RESERVE):
        raise ValueError('Native unpack custody is incomplete or mismatched')
    assembly.pin=tuple(intent['assembly_pin']);assembly.required=intent['required_bytes'];assembly.recheck()
    system.require_root()
    query=system.run(['/usr/bin/dpkg-query','--admindir='+str(assembly.root/'var/lib/dpkg'),
        '-W','-f=${Package}\t${Version}\t${Architecture}\t${Status}\n'])
    expected=sorted([row['name'],row['version'],row['architecture'],'install ok installed'] for row in manifest['components'])
    if sorted(line.split('\t') for line in query.splitlines())!=expected or p.digest(secured(assembly.work/'dpkg.log'))!=result.get('dpkg_log_sha256'):
        raise ValueError('Native unpack database/log changed before qualification')
    return assembly


class ReviewedInputs:
    """Fixed signed bundle plus reviewed generation-2 policy/map/expected image."""
    def __init__(self, kind):
        if kind not in ('base','live','mvp-base','mvp-live'):raise ValueError('Unknown reviewed image profile')
        self.kind=kind;self.base=STAGE/GENERATIONS[kind][1];self.bundle=self.base/'payload';self.recheck()

    def recheck(self):
        from runtime.installer.composition import SOURCES,source_path,validate_policy,validate_installed_handoff
        from runtime.installer.installed_boot import InstalledBoot
        p=payload_module()
        files=('payload/manifest.json','policy.json','generated-entries.json','expected-image-manifest.json','boot-profile.json')
        pins={name:p.digest(secured(self.base/name)) for name in files}
        self.source_hashes={name:p.digest(secured(source_path(name))) for name in SOURCES}
        pins.update({'source:'+name:sha for name,sha in self.source_hashes.items()})
        if hasattr(self,'pins') and self.pins!=pins:raise ValueError('Reviewed assembly input/source changed')
        self.pins=pins
        self.manifest=p.PreparedPayload(self.bundle,manifest_sha256=pins['payload/manifest.json'],runner=None,finalizer=None)._load()
        bundle_namespace(self.bundle,self.manifest)
        if hasattr(self,'kind'):check_delivery_kind(self.kind,self.manifest)
        validate_installed_handoff(self.manifest,self.source_hashes)
        self.policy=policy_input(self.base,self.manifest)
        self.generated=p.strict(secured(self.base/'generated-entries.json').read_bytes())
        self.boot=p.strict(secured(self.base/'boot-profile.json').read_bytes())
        expected=p.strict(secured(self.base/'expected-image-manifest.json').read_bytes())
        self.descriptor={'payload_manifest_sha256':pins['payload/manifest.json'],'policy_sha256':pins['policy.json'],
            'image_manifest_sha256':__import__('hashlib').sha256(p.encoded(expected)).hexdigest()}
        InstalledBoot(self.bundle,self.manifest,self.boot,None)


def finalize_native(kind, system):
    """Fresh generation 2 using real finalizer; no candidate file is promoted."""
    from runtime.installer.native_finalizer import NativeFinalizer
    p=payload_module();inputs=ReviewedInputs(kind);assembly=AssemblyRoot(kind+'-reviewed',inputs.manifest)
    write(assembly.work/'finalize-intent.json',{'version':1,'state':'native-finalizer-intended',
        'payload_manifest_sha256':inputs.descriptor['payload_manifest_sha256'],'assembly_pin':list(assembly.pin),
        'storage_budget':assembly.storage_budget,'required_bytes':assembly.required})
    observed={};finalizer=NativeFinalizer(inputs,system)
    def actual_finalizer(root,manifest):
        result=finalizer(root,manifest);observed.update(result);return result
    def stage_guard(root,plan):
        assembly.recheck()
        return Path(root)==assembly.root
    native=p.PreparedPayload(inputs.bundle,manifest_sha256=inputs.descriptor['payload_manifest_sha256'],
        runner=system,finalizer=actual_finalizer,target_guard=stage_guard)
    plan={'payload':{'sha256':inputs.descriptor['payload_manifest_sha256'],
        'catalog_sha256':inputs.manifest['catalog_sha256'],'bytes':inputs.manifest['bytes']}}
    native.install_payload(assembly.root,plan);inputs.recheck();assembly.recheck()
    result={'version':1,'state':'native-finalizer-verified','root':str(assembly.root),
        'assembly_pin':list(assembly.pin),'payload_manifest_sha256':inputs.descriptor['payload_manifest_sha256'],
        'policy_sha256':inputs.descriptor['policy_sha256'],'generated_entries_sha256':inputs.pins['generated-entries.json'],
        'image_manifest_sha256':observed['image_manifest_sha256'],'checks':observed['checks'],
        'source_sha256':inputs.source_hashes,'production_ready':False,'native_boot_verified':False}
    write(assembly.work/'finalized.json',result)
    return result


def stage_live(system,kind='live'):
    """Source-attributed live transform after real finalizer; actual journal last."""
    import live_profile
    p=payload_module();inputs=ReviewedInputs(kind)
    assembly=object.__new__(AssemblyRoot);assembly.work=STAGE/GENERATIONS[kind+'-reviewed'][0]
    assembly.root=assembly.work/reviewed_root_name(kind)
    receipt=p.strict(secured(assembly.work/'finalized.json').read_bytes())
    assembly.pin=tuple(receipt['assembly_pin']);assembly.required=RESERVE+1;assembly.recheck()
    if receipt.get('state')!='native-finalizer-verified' or receipt.get('root')!=str(assembly.root):
        raise ValueError('Actual finalized live generation required')
    media_id=live_profile.media_identity(inputs.descriptor['payload_manifest_sha256'],inputs.descriptor['policy_sha256'])
    result=live_profile.stage(assembly,inputs.manifest,inputs.policy,media_id,system)
    inputs.recheck();assembly.recheck()
    # Full metadata/hardlink snapshot is additional compression input, never a
    # substitute for NativeFinalizer + the live transform's exact delta audit.
    sys.path[:0]=[str(ROOT/'scripts/build/h10'),str(ROOT/'scripts/build')]
    from copy_selected_root import snapshot,tree_names
    from acl_sidecar import stage_acl
    import subprocess
    class NativeRootBackend:
        native=True
        target=Path('/')
        def run(self,program,*arguments,**kwargs):
            if program not in ('dpkg-query','bash'):raise ValueError('Unknown fixed ACL native program')
            return subprocess.run(['/usr/bin/env','-i','HOME=/root','PATH=/usr/bin:/usr/sbin','LC_ALL=C',
                '/usr/bin/'+program,*arguments],check=True,**kwargs)
    acl=stage_acl(NativeRootBackend(),assembly.root,inputs.bundle/'records')
    write(assembly.work/'acl-report.json',acl)
    image=snapshot(assembly.root,tree_names(assembly.root))
    evidence=assembly.work/'evidence';evidence.mkdir(mode=0o700)
    write(evidence/'image-manifest.json',image)
    external=lambda path:Path('/mnt/lfs')/path.relative_to('/')
    journal={'assembled':True,'release_profile':True,'release_accepted':False,'installer_ready':False,
        'native_kernel_boot_verified':False,'image':str(external(assembly.root)),
        'evidence':str(external(evidence)),'native_image':str(assembly.root),
        'assembler_sha256':p.digest(Path(__file__)),'payload_manifest_sha256':inputs.descriptor['payload_manifest_sha256'],
        'native_finalizer_receipt_sha256':p.digest(secured(assembly.work/'finalized.json')),
        'live_profile_receipt_sha256':p.digest(secured(assembly.work/'live-profile-receipt.json')),
        'acl_report_sha256':p.digest(secured(assembly.work/'acl-report.json')),
        'media_id':media_id,'actions':[{'step':'image-manifest','finished':True,
            'report':'image-manifest.json','sha256':p.digest(evidence/'image-manifest.json')}]}
    if kind.startswith('mvp-'):journal.update(delivery_class=MVP_CLASS,g2_eligible=False)
    write(evidence/'assembly.json',journal)
    return {'state':'source-attributed-live-image-media-inputs','journal':str(external(evidence/'assembly.json')),
        'native_kernel_boot_verified':False,'release_accepted':False,'live_profile':result}


def unclosed_compiler_jobs(directory):
    """Recognize job.py harness records only, not unrelated custom JSON receipts."""
    import re
    result=[]
    harnesses={'/opt/toddy-build/scripts/build/phase2/'+name for name in
        ('isolated.sh','cups-isolated.sh','samba-isolated.sh')}
    required={'pid','boot_id','proc_start_ticks','started_unix','command','harness_sha256'}
    for path in sorted(Path(directory).glob('*.job.json')):
        if path.is_symlink() or path.stat().st_size>256*1024:continue
        try:record=json.loads(path.read_bytes())
        except (ValueError,UnicodeError):continue
        if not isinstance(record,dict) or not required<=record.keys():continue
        if type(record['pid']) is not int or record['pid']<=0 or not isinstance(record['harness_sha256'],str) or not re.fullmatch('[a-f0-9]{64}',record['harness_sha256']):continue
        command=record['command']
        if not isinstance(command,list) or len(command)<6 or not all(isinstance(value,str) for value in command) or command[0]!='/bin/bash' or command[1] not in harnesses:continue
        offset=3 if command[2]=='--loopback' else 2
        if len(command)<=offset+2 or not all(isinstance(command[x],str) for x in (offset,offset+1)):continue
        if not command[offset].startswith('/mnt/lfs/sources/phase2/inputs/') or not command[offset+1].startswith('/mnt/lfs/sources/phase2/work/'):continue
        name=path.name.removesuffix('.job.json')
        if not re.fullmatch('[a-z][a-z0-9-]{1,63}',name):continue
        if not (path.parent/(name+'.exit')).is_file():result.append(name)
    return result


def main():
    if (sys.argv[1:] not in ([action] for action in ('base','live','qualify-base','qualify-live','finalize-base','finalize-live','stage-live',
            'mvp-base','mvp-live','qualify-mvp-base','qualify-mvp-live','finalize-mvp-base','finalize-mvp-live','stage-mvp-live')) or
            Path(__file__).resolve() != Path('/opt/toddy-build/scripts/build/phase2/image_assemble.py')):
        raise ValueError('Fixed native source coordinator command required')
    os.umask(0o077); system=LinuxDisk();native_guard(system)
    descriptor = os.open('/run/toddy-image-assembly.lock', os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW, 0o600)
    try:
        info=os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode) or info.st_uid or info.st_gid or info.st_nlink!=1 or stat.S_IMODE(info.st_mode)!=0o600:
            raise ValueError('Native assembly lock custody')
        fcntl.flock(descriptor, fcntl.LOCK_EX|fcntl.LOCK_NB)
        action=sys.argv[1];kind=action.removeprefix('qualify-').removeprefix('finalize-').removeprefix('stage-');bundle=STAGE/GENERATIONS[kind][1]/'payload';p=payload_module()
        sha=p.digest(secured(bundle/'manifest.json'))
        manifest=p.PreparedPayload(bundle,manifest_sha256=sha,runner=None,finalizer=None)._load()
        bundle_namespace(bundle,manifest)
        if action in ('stage-live','stage-mvp-live'):
            result=stage_live(system,kind)
        elif action.startswith('finalize-'):
            result=finalize_native(kind,system)
        elif action.startswith('qualify-'):
            from resource_recipe import qualify
            policy=policy_input(bundle.parent,manifest)
            assembly=adopt_unpacked(kind,manifest,sha,system)
            result=qualify(assembly,manifest,policy,system)
        else:
            assembly=AssemblyRoot(kind,manifest)
            result=unpack_native(bundle,sha,assembly,system)
        print(json.dumps(result,sort_keys=True))
    finally:
        os.close(descriptor)


if __name__ == '__main__':
    main()

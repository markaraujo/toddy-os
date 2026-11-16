"""Custody of a fixed native installer composition, never a callback selector."""
import hashlib
import os
from pathlib import Path
import re
import stat
from .disk_plan import InstallError
from .native_finalizer import payload_module,NativeFinalizer,account_files
from .installed_boot import InstalledBoot,RELEASE

BASE=Path('/usr/share/toddy/installer/composition')
SOURCES={'generated_resources.py','live_bindings.py','composition.py','native_finalizer.py','installed_boot.py','setup/installer_handoff.py',
         'offline_payload.py','h10/initramfs_runtime.py','h10/initramfs_archive.py','audit_native_elf.py',
         'backend.py','disk_plan.py','installed_identity.py','linux_disk.py','launch.py','calamares/adapter.py','calamares/cli.py',
         'setup/pending.py','shared/json.py'}
HASH=re.compile('[0-9a-f]{64}\\Z')


def secured(path,limit=256*1024*1024):
    path=Path(path)
    if not path.is_absolute() or path.resolve()!=path:raise InstallError('installer_composition_redirected')
    for ancestor in (*path.parents,):
        info=ancestor.lstat()
        if not stat.S_ISDIR(info.st_mode) or info.st_uid!=0 or info.st_mode&0o022:raise InstallError('installer_composition_directory_custody')
    info=path.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_uid!=0 or info.st_gid!=0 or info.st_nlink!=1 or info.st_mode&0o022 or info.st_size>limit:
        raise InstallError('installer_composition_file_custody')
    return path


def source_path(relative):
    here=Path(__file__).resolve().parent
    if relative.startswith(('setup/','shared/')):return here.parent/relative
    if relative=='offline_payload.py' and not (here/relative).is_file():return here.parents[1]/'scripts/build/phase2/offline_payload.py'
    if relative.startswith('h10/') and not (here/relative).is_file():return here.parents[1]/'scripts/build'/relative
    if relative=='audit_native_elf.py' and not (here/relative).is_file():return here.parents[1]/'scripts/build/audit_native_elf.py'
    return here/relative


def validate_installed_handoff(manifest,source_hashes):
    for target,name in (('/usr/lib/toddy/setup/installer_handoff.py','setup/installer_handoff.py'),
                        ('/usr/lib/toddy/setup/pending.py','setup/pending.py'),
                        ('/usr/lib/toddy/shared/json.py','shared/json.py')):
        if manifest['ownership']['entries'].get(target,{}).get('sha256')!=source_hashes[name]:
            raise InstallError('installer_composition_installed_handoff_source')


def validate_policy(policy,manifest):
    p=payload_module()
    if not isinstance(policy,dict) or set(policy)!={'accounts','required_policy_paths'} or not isinstance(policy['required_policy_paths'],list) or not 1<=len(policy['required_policy_paths'])<=256:
        raise InstallError('installer_composition_policy')
    account_files(policy['accounts'])
    for path in policy['required_policy_paths']:
        p.canonical(path)
        if not path.startswith(('/etc/pam.d/','/usr/lib/systemd/system/','/etc/systemd/system/')) or not manifest['ownership']['entries'].get(path,{}).get('sha256'):
            raise InstallError('installer_composition_unowned_policy')


def bundle_namespace(directory,manifest):
    p=payload_module();directory=Path(directory)
    files={'manifest.json','preparation-state.json','profile.json','projection.json','catalog.json',
           'repository/trusted-keyring.gpg','repository/Release','repository/Release.gpg','repository/Packages'}
    for component in manifest['components']:
        for parent,key in (('archives','archive'),('records','record')):
            p.canonical(component[key],absolute=False)
            if '/' in component[key]:raise InstallError('installer_composition_payload_name')
            files.add(parent+'/'+component[key])
    observed_files=set();observed_dirs=set()
    for base,directories,leaves in os.walk(directory,followlinks=False):
        for leaf in directories:
            path=Path(base)/leaf
            if path.is_symlink():raise InstallError('installer_composition_redirected_payload')
            observed_dirs.add(path.relative_to(directory).as_posix())
        for leaf in leaves:observed_files.add((Path(base)/leaf).relative_to(directory).as_posix())
    if observed_files!=files or observed_dirs!={'archives','records','repository'}:
        raise InstallError('installer_composition_unselected_payload_state')


class Composition:
    def __init__(self):
        # The production constructor has no data path, hook, trust/key or policy
        # override. Low-level helpers remain independently testable build code.
        self.base=BASE;self.bundle=BASE/'payload'
        self.recheck()

    def read(self,name,expected=None):
        p=payload_module();path=secured(self.base/name)
        if expected is not None and p.digest(path)!=expected:raise InstallError('installer_composition_input_changed')
        return p.strict(path.read_bytes())

    def recheck(self):
        p=payload_module()
        expected={'composition.json','payload','policy.json','boot-profile.json','generated-entries.json','qualification.json','qualification'}
        if {path.name for path in self.base.iterdir()}!=expected:raise InstallError('installer_composition_unselected_state')
        allowed_reports={name+'.json' for name in p.CHECKS}|{'boot-bios.json','boot-uefi.json'}
        if any(path.name not in allowed_reports for path in (self.base/'qualification').iterdir()):raise InstallError('installer_composition_unselected_report')
        descriptor=self.read('composition.json')
        keys={'schema_version','payload_manifest_sha256','catalog_sha256','policy_sha256','generated_entries_sha256',
              'image_manifest_sha256','boot_profile_sha256','qualification_sha256','source_sha256'}
        if not isinstance(descriptor,dict) or set(descriptor)!=keys or type(descriptor['schema_version']) is not int or descriptor['schema_version']!=1 or \
                any(not isinstance(descriptor[key],str) or not HASH.fullmatch(descriptor[key]) for key in keys-{'schema_version','source_sha256'}):raise InstallError('installer_composition_schema')
        if not isinstance(descriptor['source_sha256'],dict) or set(descriptor['source_sha256'])!=SOURCES:raise InstallError('installer_composition_source_closure')
        for name,expected in descriptor['source_sha256'].items():
            if not isinstance(expected,str) or not HASH.fullmatch(expected) or p.digest(secured(source_path(name)))!=expected:raise InstallError('installer_composition_source_changed')
        if hasattr(self,'descriptor') and self.descriptor!=descriptor:raise InstallError('installer_composition_changed_during_operation')
        self.descriptor=descriptor
        self.policy=self.read('policy.json',descriptor['policy_sha256'])
        if not isinstance(self.policy,dict) or set(self.policy)!={'accounts','required_policy_paths'} or not isinstance(self.policy['required_policy_paths'],list):raise InstallError('installer_composition_policy')
        account_files(self.policy['accounts'])
        self.generated=self.read('generated-entries.json',descriptor['generated_entries_sha256'])
        if not isinstance(self.generated,dict):raise InstallError('installer_composition_generated_entries')
        for name,row in self.generated.items():
            p.canonical(name)
            if not isinstance(row,dict) or row.get('origin') not in p.CHECKS|{'fresh-filesystem'}:raise InstallError('installer_composition_generated_origin')
        self.boot=self.read('boot-profile.json',descriptor['boot_profile_sha256'])
        # The native payload loader independently rechecks signed Release, key
        # pin, every archive/record, profile and projection. No verified marker.
        if self.bundle.resolve()!=self.bundle or not self.bundle.is_dir():raise InstallError('installer_composition_payload_directory')
        for base,directories,files in os.walk(self.bundle,followlinks=False):
            for leaf in directories:
                directory=Path(base)/leaf;info=directory.lstat()
                if not stat.S_ISDIR(info.st_mode) or info.st_uid!=0 or info.st_gid!=0 or info.st_mode&0o022:raise InstallError('installer_composition_payload_directory')
            for leaf in files:secured(Path(base)/leaf,limit=8*1024**3)
        manifest=p.PreparedPayload(self.bundle,manifest_sha256=descriptor['payload_manifest_sha256'],runner=None,finalizer=None)._load()
        bundle_namespace(self.bundle,manifest)
        validate_policy(self.policy,manifest)
        if manifest['catalog_sha256']!=descriptor['catalog_sha256']:raise InstallError('installer_composition_catalog')
        validate_installed_handoff(manifest,descriptor['source_sha256'])
        self.manifest=manifest

    def readiness(self):
        self.recheck();p=payload_module();descriptor=self.descriptor
        report=self.read('qualification.json',descriptor['qualification_sha256'])
        if not isinstance(report,dict) or set(report)!={'kind','input_manifest_sha256','source_sha256','image_manifest_sha256','checks','firmware_reports'} or \
                report['kind']!='native-installer-composition-v1' or report['input_manifest_sha256']!=descriptor['payload_manifest_sha256'] or \
                report['source_sha256']!=descriptor['source_sha256'] or report['image_manifest_sha256']!=descriptor['image_manifest_sha256'] or \
                not isinstance(report['checks'],dict) or set(report['checks'])!=p.CHECKS or not isinstance(report['firmware_reports'],dict) or \
                not report['firmware_reports'] or set(report['firmware_reports'])-{'bios','uefi'}:
            raise InstallError('installer_native_composition_not_qualified')
        for name,digest in report['checks'].items():
            value=self.read('qualification/'+name+'.json',digest)
            validate_finalizer_report(value,name,descriptor)
        for firmware,digest in report['firmware_reports'].items():
            value=self.read('qualification/boot-'+firmware+'.json',digest)
            validate_boot_evidence(value,firmware,descriptor,self.boot)
        sourcehash=hashlib.sha256(p.encoded(descriptor['source_sha256'])).hexdigest()
        return {'verified':True,'payload_manifest_sha256':descriptor['payload_manifest_sha256'],
                'catalog_sha256':descriptor['catalog_sha256'],'finalizer_source_sha256':sourcehash,
                'native_qualification_report_sha256':descriptor['qualification_sha256'],
                'supported_firmware':sorted(report['firmware_reports'])}



def validate_finalizer_report(value,name,descriptor):
    required={
        'native-dpkg-database':{'configured_packages','database_audit_empty'},
        'fresh-system-accounts':{'account_policy_sha256','locked_accounts','fresh_files'},
        'pam-service-policy':{'selected_owned_policy_files','policy_sha256','default_target','display_manager'},
        'generated-caches':{'native_commands','qualified_cache_outputs'},
        'private-state-and-keys':{'fresh_account_policy','root_and_home_empty','known_secret_namespaces_empty','complete_image_bound_to_qualified_projection'},
        'runtime-linkage':{'native_elf_consumers','unresolved_dependencies'},
        'ownership-xattrs':{'entries','unreviewed_xattrs','cross_device_entries'},
        'whole-image-attribution':{'image_manifest_sha256','entries'},
        'foundation-recovery':{'source_owned_recovery_paths','unchanged'}}
    if not isinstance(value,dict) or set(value)!={'check','input_manifest_sha256','passed','exit_status','postconditions'} or \
            value['check']!=name or value['input_manifest_sha256']!=descriptor['payload_manifest_sha256'] or value['passed'] is not True or \
            type(value['exit_status']) is not int or value['exit_status']!=0 or not isinstance(value['postconditions'],dict) or set(value['postconditions'])!=required[name]:
        raise InstallError('installer_native_finalizer_receipt')
    post=value['postconditions']
    for key in ('configured_packages','locked_accounts','fresh_files','selected_owned_policy_files','native_commands','entries'):
        if key in post and (type(post[key]) is not int or post[key]<=0):raise InstallError('installer_native_finalizer_measurement')
    for key in ('qualified_cache_outputs','unresolved_dependencies','unreviewed_xattrs','cross_device_entries'):
        if key in post and (type(post[key]) is not int or post[key]<0 or key!='qualified_cache_outputs' and post[key]!=0):raise InstallError('installer_native_finalizer_measurement')
    for key in ('database_audit_empty','fresh_account_policy','root_and_home_empty','known_secret_namespaces_empty','unchanged'):
        if key in post and post[key] is not True:raise InstallError('installer_native_finalizer_postcondition')
    for key,target in (('account_policy_sha256','policy_sha256'),('policy_sha256','policy_sha256'),
                       ('image_manifest_sha256','image_manifest_sha256'),('complete_image_bound_to_qualified_projection','image_manifest_sha256')):
        if key in post and post[key]!=descriptor[target]:raise InstallError('installer_native_finalizer_binding')
    if name=='runtime-linkage' and post['native_elf_consumers']!=['/usr/bin/bash','/usr/bin/python3','/usr/bin/gnome-shell','/usr/sbin/gdm']:raise InstallError('installer_native_finalizer_runtime_scope')
    if name=='pam-service-policy' and (post['default_target']!='graphical.target' or post['display_manager']!='gdm.service'):raise InstallError('installer_native_finalizer_service_scope')
    if name=='foundation-recovery' and post['source_owned_recovery_paths']!=list(payload_module().RECOVERY_PATHS):raise InstallError('installer_native_finalizer_recovery_scope')

def validate_boot_evidence(value,firmware,descriptor,boot):
    required={'kind','firmware','input_manifest_sha256','image_manifest_sha256','kernel_sha256','initramfs_source_sha256','boots'}
    if not isinstance(value,dict) or set(value)!=required or value['kind']!='native-detached-installed-boot-v1' or \
            value['firmware']!=firmware or value['input_manifest_sha256']!=descriptor['payload_manifest_sha256'] or \
            value['image_manifest_sha256']!=descriptor['image_manifest_sha256'] or value['kernel_sha256']!=boot['kernel_sha256'] or \
            value['initramfs_source_sha256']!=descriptor['source_sha256']['installed_boot.py'] or not isinstance(value['boots'],list) or len(value['boots'])!=2:
        raise InstallError('installer_native_boot_receipt')
    seen=set();persistent=None;root_uuid=None;initramfs=None
    for row in value['boots']:
        if not isinstance(row,dict) or set(row)!={'boot_id','root_uuid','persistent_marker_sha256','kernel_release','installer_media_attached','fresh_owner_login','initramfs_sha256'} or \
                not isinstance(row['boot_id'],str) or not re.fullmatch('[a-f0-9-]{36}',row['boot_id']) or row['boot_id'] in seen or \
                not isinstance(row['root_uuid'],str) or not re.fullmatch('[A-Fa-f0-9-]{4,40}',row['root_uuid']) or \
                not isinstance(row['persistent_marker_sha256'],str) or not HASH.fullmatch(row['persistent_marker_sha256']) or \
                not isinstance(row['initramfs_sha256'],str) or not HASH.fullmatch(row['initramfs_sha256']) or \
                row['kernel_release']!=RELEASE or row['installer_media_attached'] is not False or row['fresh_owner_login'] is not True:
            raise InstallError('installer_native_detached_boot_postconditions')
        seen.add(row['boot_id'])
        if persistent is not None and (persistent!=row['persistent_marker_sha256'] or root_uuid!=row['root_uuid'] or initramfs!=row['initramfs_sha256']):raise InstallError('installer_native_persistence_receipt')
        persistent=row['persistent_marker_sha256'];root_uuid=row['root_uuid'];initramfs=row['initramfs_sha256']


def validate_owner_options(policy,options):
    if not isinstance(options,dict) or not isinstance(options.get('username'),str) or \
            not re.fullmatch('[a-z][a-z0-9_-]{0,31}',options['username']) or options['username'] in ('root','lfs','tester','builder','toddy','toddy-live') or \
            type(options.get('uid')) is not int or type(options.get('gid')) is not int or \
            not 1000<=options['uid']<=60000 or not 1000<=options['gid']<=60000:
        raise InstallError('installer_owner_identity')
    accounts=policy['accounts']
    users=[row.split(':') for row in accounts['passwd'].splitlines()]
    groups=[row.split(':') for row in accounts['group'].splitlines()]
    if any(row[0]==options['username'] or int(row[2])==options['uid'] for row in users) or \
            any(row[0]==options['username'] or int(row[2])==options['gid'] for row in groups):
        raise InstallError('installer_owner_collides_with_system_account')


class ComposedPayload:
    def __init__(self,composition,native):self.composition=composition;self.native=native

    def verify_payload(self,plan):
        self.composition.readiness()
        validate_owner_options(self.composition.policy,plan['options'])
        return self.native.verify_payload(plan)

    def install_payload(self,root,plan):
        self.verify_payload(plan)
        return self.native.install_payload(root,plan)

    def _load(self):return self.native._load()


class LiveBindings:
    def __init__(self,composition,system):
        from .disk_plan import ProductionPolicy
        p=payload_module();self.composition=composition;self.system=system;self.policy=ProductionPolicy()
        composition.readiness()
        self.payload=ComposedPayload(composition,p.PreparedPayload(composition.bundle,manifest_sha256=composition.descriptor['payload_manifest_sha256'],
                                       runner=system,finalizer=NativeFinalizer(composition,system)))
        self.build_boot=InstalledBoot(composition.bundle,composition.manifest,composition.boot,system)

    def readiness(self):return self.composition.readiness()

    def validate_options(self,options):
        self.composition.readiness()
        validate_owner_options(self.composition.policy,options)

    def payload_identity(self):
        self.readiness();manifest=self.payload._load()
        return {'sha256':self.composition.descriptor['payload_manifest_sha256'],'catalog_sha256':manifest['catalog_sha256'],'bytes':manifest['bytes']}

    def save_pending(self,root,plan):
        self.readiness();options=plan['options']
        request={key:options[key] for key in ('operation_id','uid','gid','username','ai_choice','extras')}
        request['catalog_sha256']=plan['payload']['catalog_sha256']
        command=['/usr/bin/chroot','--userspec='+str(options['uid'])+':'+str(options['gid']),'--groups='+str(options['gid']),str(root),
                 '/usr/bin/env','-i','PATH=/usr/bin:/usr/sbin','HOME=/home/'+options['username'],'LANG=C.UTF-8',
                 '/usr/bin/python3','-I','/usr/lib/toddy/setup/installer_handoff.py']
        result=self.system.run(command,data=payload_module().encoded(request))
        return payload_module().strict(result.encode())

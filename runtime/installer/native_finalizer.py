"""Fixed native archive-root finalization and independently attributed readback."""
import hashlib
import os
from pathlib import Path
import re
import stat
from .disk_plan import InstallError
from .installed_identity import regular
from .generated_resources import generate_loader_cache


def payload_module():
    try:from . import offline_payload
    except ImportError:from scripts.build.phase2 import offline_payload
    return offline_payload


def account_files(baseline):
    if not isinstance(baseline,dict) or set(baseline)!={'passwd','group'} or not isinstance(baseline.get('passwd'),str) or not isinstance(baseline.get('group'),str):
        raise InstallError('installer_account_baseline')
    users=[line.split(':') for line in baseline['passwd'].splitlines()]
    groups=[line.split(':') for line in baseline['group'].splitlines()]
    if not users or any(len(row)!=7 for row in users) or any(len(row)!=4 for row in groups):raise InstallError('installer_account_baseline')
    names={row[0] for row in users};gids={row[2] for row in groups}
    if len(names)!=len(users) or len({row[2] for row in users})!=len(users) or len({row[0] for row in groups})!=len(groups) or len(gids)!=len(groups):raise InstallError('installer_account_duplicates')
    if not any(row==['wheel','x','97',''] for row in groups):raise InstallError('installer_fresh_wheel_baseline')
    if users[0]!=['root','x','0','0','root','/root','/bin/bash'] or not any(row==['root','x','0',''] for row in groups):raise InstallError('installer_account_root')
    for row in users:
        if not re.fullmatch('[a-z_][a-z0-9_-]*',row[0]) or row[0] in ('lfs','tester','builder','toddy','toddy-live') or row[1]!='x' or not row[2].isdigit() or row[3] not in gids or \
                (row[0]!='root' and (not (1<=int(row[2])<1000 or int(row[2])==65534) or row[6] not in ('/usr/bin/false','/bin/false','/usr/sbin/nologin'))):
            raise InstallError('installer_inherited_account')
    for row in groups:
        if not re.fullmatch('[a-z_][a-z0-9_-]*',row[0]) or row[1]!='x' or not row[2].isdigit() or (row[0]!='root' and int(row[2])==0) or any(name not in names for name in row[3].split(',') if name):raise InstallError('installer_account_group')
    return {'etc/passwd':(baseline['passwd'].encode(),0o644),'etc/group':(baseline['group'].encode(),0o644),
            'etc/shadow':(''.join(row[0]+':!:::::::\n' for row in users).encode(),0o600),
            'etc/gshadow':(''.join(row[0]+':!::'+row[3]+'\n' for row in groups).encode(),0o600),
            'etc/subuid':(b'',0o644),'etc/subgid':(b'',0o644),'etc/machine-id':(b'',0o444)}


def cache_command(path,tool):
    """Closed native argv vocabulary; declarative data cannot provide commands."""
    payload_module().canonical(path);payload_module().canonical(tool)
    parent=str(Path(path).parent)
    if path.endswith('/gschemas.compiled') and tool=='/usr/bin/glib-compile-schemas':return [tool,'--strict',parent]
    if path.endswith('/icon-theme.cache') and tool in ('/usr/bin/gtk4-update-icon-cache','/usr/bin/gtk-update-icon-cache'):return [tool,'--force','--ignore-theme-index',parent]
    if path=='/usr/share/mime/mime.cache' and tool=='/usr/bin/update-mime-database':return [tool,'/usr/share/mime']
    if path.endswith('/giomodule.cache') and tool=='/usr/bin/gio-querymodules':return [tool,parent]
    if path=='/usr/lib/udev/hwdb.bin' and tool=='/usr/bin/systemd-hwdb':return [tool,'update','--usr']
    if Path(path).parent==Path('/etc/dconf/db') and not path.endswith('.d') and tool=='/usr/bin/dconf':
        return [tool,'compile',path,path+'.d']
    if path.startswith('/usr/lib/modules/7.1.8-toddy/modules.') and tool=='/usr/sbin/depmod':return [tool,'-a','7.1.8-toddy']
    # kmod34.2 dispatches compatibility commands from argv[0], not a subcommand.
    # Frozen Coreutils env supports --argv0; both regular executables are checked.
    if path.startswith('/usr/lib/modules/7.1.8-toddy/modules.') and tool=='/usr/bin/kmod':return ['/usr/bin/env','--argv0=depmod',tool,'-a','7.1.8-toddy']
    if re.fullmatch(r'/usr/lib/gdk-pixbuf-2\.0/[0-9.]+/loaders\.cache',path) and tool in ('/usr/bin/gdk-pixbuf-query-loaders','/usr/lib/gdk-pixbuf-2.0/gdk-pixbuf-query-loaders'):
        return [tool,'--update-cache']
    if re.fullmatch(r'/usr/lib/gtk-[234]\.0/[0-9.]+/immodules\.cache',path) and tool in ('/usr/bin/gtk-query-immodules-3.0','/usr/bin/gtk-query-immodules-2.0'):
        return [tool,'--update-cache']
    # Unknown families remain unqualified; never invent output or copy a cache.
    raise InstallError('installer_cache_native_recipe_unqualified')


def cache_executables(path,tool):
    command=cache_command(path,tool)
    return ['/usr/bin/env',tool] if command[0]=='/usr/bin/env' else [tool]


def verify_cache_executables(root,path,binding,entries):
    p=payload_module();tool=binding['tool']
    if entries.get(tool['path'],{}).get('sha256')!=tool['sha256']:raise InstallError('installer_finalizer_cache_tool_changed')
    for executable in cache_executables(path,tool['path']):
        source=Path(root)/executable.lstrip('/');expected=entries.get(executable,{}).get('sha256')
        if not expected or source.parent.resolve()!=source.parent or source.is_symlink() or p.digest(source)!=expected:raise InstallError('installer_finalizer_cache_tool_changed')


def fresh_directory(root,relative,row):
    """Create declared numeric ownership; never normalize an existing mismatch."""
    p=payload_module();p.canonical('/'+relative);root=Path(root);path=root/relative
    if (set(row)!={'mode','uid','gid','directory'} or row.get('directory') is not True or
            type(row.get('mode')) is not int or not stat.S_ISDIR(row['mode']) or row['mode']!=(stat.S_IFDIR|stat.S_IMODE(row['mode'])) or
            any(type(row.get(key)) is not int or not 0<=row[key]<2**32-1 for key in ('uid','gid')) or
            root.resolve()!=root or path.parent.resolve()!=path.parent):raise InstallError('installer_finalizer_fresh_directory')
    try:path.mkdir(mode=stat.S_IMODE(row['mode']))
    except FileExistsError:pass
    else:
        os.chown(path,row['uid'],row['gid'],follow_symlinks=False)
        path.chmod(stat.S_IMODE(row['mode']))
    info=path.lstat()
    if (info.st_mode,info.st_uid,info.st_gid,info.st_dev)!=(row['mode'],row['uid'],row['gid'],root.stat().st_dev):raise InstallError('installer_finalizer_fresh_directory')


class NativeFinalizer:
    def __init__(self,composition,system):self.composition=composition;self.system=system

    def __call__(self,root,manifest):
        p=payload_module();root=Path(root);self.system.require_root()
        composition=self.composition;composition.recheck()
        if p.digest(composition.bundle/'manifest.json')!=composition.descriptor['payload_manifest_sha256']:
            raise InstallError('installer_finalizer_payload_changed')
        run=Path('/run/toddy-installer')/('finalization-'+root.name)
        parent=run.parent.lstat()
        if run.parent.resolve()!=run.parent or not stat.S_ISDIR(parent.st_mode) or parent.st_uid!=0 or parent.st_gid!=0 or stat.S_IMODE(parent.st_mode)!=0o700:
            raise InstallError('installer_finalizer_private_report_directory')
        if run.exists() or run.is_symlink():raise InstallError('installer_finalizer_reconciliation_required')
        run.mkdir(mode=0o700)
        observed={}
        def record(check,postconditions):
            report={'check':check,'input_manifest_sha256':composition.descriptor['payload_manifest_sha256'],
                    'passed':True,'exit_status':0,'postconditions':postconditions}
            path=run/(check+'.json');path.write_bytes(p.encoded(report));path.chmod(0o600)
            observed[check]={'passed':True,'exit_status':0,'report':str(path),'report_sha256':p.digest(path)}
        query=self.system.run(['/usr/bin/dpkg-query','--admindir='+str(root/'var/lib/dpkg'),'-W','-f=${Package}\t${Version}\t${Architecture}\t${Status}\n'])
        rows=[line.split('\t') for line in query.splitlines()]
        expected=sorted([row['name'],row['version'],row['architecture'],'install ok installed'] for row in manifest['components'])
        if sorted(rows)!=expected:raise InstallError('installer_finalizer_native_database')
        if self.system.run(['/usr/bin/dpkg','--root='+str(root),'--audit']):raise InstallError('installer_finalizer_native_audit')
        record('native-dpkg-database',{'configured_packages':len(rows),'database_audit_empty':True})
        fresh=manifest['ownership']['fresh_directories']
        for relative,row in sorted(fresh.items(),key=lambda item:(item[0].count('/'),item[0])):
            fresh_directory(root,relative,row)
        files=account_files(composition.policy['accounts'])
        for relative,(data,mode) in files.items():
            path=root/relative
            if path.exists() or path.is_symlink():raise InstallError('installer_finalizer_inherited_account_file')
            regular(root,relative,data,mode)
        record('fresh-system-accounts',{'account_policy_sha256':composition.descriptor['policy_sha256'],
                                     'locked_accounts':len(composition.policy['accounts']['passwd'].splitlines()),'fresh_files':len(files)})
        required=composition.policy['required_policy_paths']
        if not required or any(not (path.startswith('/etc/pam.d/') or path.startswith('/usr/lib/systemd/system/') or path.startswith('/etc/systemd/system/')) for path in required):raise InstallError('installer_finalizer_policy_scope')
        for virtual in required:
            p.canonical(virtual);expected=manifest['ownership']['entries'].get(virtual);path=root/virtual.lstrip('/')
            if not expected or not expected.get('sha256') or path.parent.resolve()!=path.parent or path.is_symlink() or p.digest(path)!=expected['sha256']:raise InstallError('installer_finalizer_policy_unowned')
        for virtual,target in (('/etc/systemd/system/default.target','/usr/lib/systemd/system/graphical.target'),
                               ('/etc/systemd/system/display-manager.service','/usr/lib/systemd/system/gdm.service')):
            expected={'mode':stat.S_IFLNK|0o777,'uid':0,'gid':0,'symlink':target}
            generated=composition.generated.get(virtual,{})
            if manifest['ownership']['entries'].get(virtual)!=expected and generated!={**expected,'origin':'pam-service-policy'}:
                raise InstallError('installer_finalizer_login_service_attribution')
            if not manifest['ownership']['entries'].get(target,{}).get('sha256'):raise InstallError('installer_finalizer_login_service_unowned')
            path=root/virtual.lstrip('/')
            if path.parent.resolve()!=path.parent:raise InstallError('installer_finalizer_login_service_parent')
            if path.exists() or path.is_symlink():
                if not path.is_symlink() or os.readlink(path)!=target:raise InstallError('installer_finalizer_live_service_conflict')
            else:os.symlink(target,path)
        record('pam-service-policy',{'selected_owned_policy_files':len(required),'policy_sha256':composition.descriptor['policy_sha256'],
                                     'default_target':'graphical.target','display_manager':'gdm.service'})
        commands=set()
        for virtual,binding in sorted(manifest['generated']['owned_cache_bindings'].items()):
            verify_cache_executables(root,virtual,binding,manifest['ownership']['entries'])
            command=cache_command(virtual,binding['tool']['path'])
            if tuple(command) not in commands:
                self.system.run(['/usr/sbin/chroot',str(root),*command],timeout=120);commands.add(tuple(command))
            path=root/virtual.lstrip('/')
            if path.is_symlink() or p.digest(path)!=binding['output_sha256']:raise InstallError('installer_finalizer_cache_differs')
        loader=generate_loader_cache(root,manifest['ownership']['entries'],self.system)
        loader_receipt=run/'loader-cache.json'
        loader_receipt.write_bytes(p.encoded(loader));loader_receipt.chmod(0o600)
        record('generated-caches',{'native_commands':len(commands)+loader['native_commands'],'qualified_cache_outputs':len(manifest['generated']['owned_cache_bindings'])})
        forbidden=('root/.ssh','root/.gnupg','root/.bash_history','var/lib/systemd/random-seed','var/lib/systemd/credential.secret','var/lib/toddy-executor','var/lib/toddy/executor','var/lib/toddy/installer','etc/apt/auth.conf')
        if any((root/path).exists() or (root/path).is_symlink() for path in forbidden) or any((root/'root').iterdir()) or any((root/'home').iterdir()):raise InstallError('installer_finalizer_private_state')
        for relative in ('etc/NetworkManager/system-connections','etc/apt/auth.conf.d','etc/ssl/private'):
            path=root/relative
            if path.is_symlink() or path.exists() and (not path.is_dir() or any(path.iterdir())):raise InstallError('installer_finalizer_private_state')
        record('private-state-and-keys',{'fresh_account_policy':True,'root_and_home_empty':True,'known_secret_namespaces_empty':True,
                                         'complete_image_bound_to_qualified_projection':composition.descriptor['image_manifest_sha256']})
        consumers=('/usr/bin/bash','/usr/bin/python3','/usr/bin/gnome-shell','/usr/sbin/gdm')
        runtime,_=__import__(__package__+'.installed_boot',fromlist=['machinery']).machinery()
        for virtual in consumers:
            source,canonical=runtime.target_resolve(root,virtual)
            if canonical not in manifest['ownership']['entries'] or source.is_symlink() or p.digest(source)!=manifest['ownership']['entries'][canonical].get('sha256'):raise InstallError('installer_finalizer_runtime_owner')
            runtime.runtime_dependencies(root,virtual)
        record('runtime-linkage',{'native_elf_consumers':list(consumers),'unresolved_dependencies':0})
        snapshot=p.PreparedPayload.audit_tree(root,manifest,composition.generated)
        actual=hashlib.sha256(p.encoded(snapshot)).hexdigest()
        if actual!=composition.descriptor['image_manifest_sha256']:raise InstallError('installer_finalizer_image_differs')
        record('ownership-xattrs',{'entries':len(snapshot),'unreviewed_xattrs':0,'cross_device_entries':0})
        record('whole-image-attribution',{'image_manifest_sha256':actual,'entries':len(snapshot)})
        for virtual in manifest['required_recovery_paths']:
            if snapshot.get(virtual)!=manifest['ownership']['entries'][virtual]:raise InstallError('installer_finalizer_recovery_changed')
        record('foundation-recovery',{'source_owned_recovery_paths':manifest['required_recovery_paths'],'unchanged':True})
        return {'checks':observed,'generated_entries':composition.generated,'image_manifest_sha256':actual}

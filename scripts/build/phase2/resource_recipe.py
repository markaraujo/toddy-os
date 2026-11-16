"""First native candidate resources; never a production finalizer/readiness bypass.

The coordinator supplies an inode-pinned, freshly unpacked AssemblyRoot. Actual
native output is captured for independent review. Only another fresh root may
subsequently use reviewed exact entries with the production NativeFinalizer.
"""
import hashlib
import os
from pathlib import Path
import re
import stat
import sys

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from runtime.installer.native_finalizer import account_files,cache_command,payload_module
from runtime.installer.generated_resources import generate_loader_cache
from runtime.installer.installed_identity import regular
from runtime.installer.composition import validate_policy

LINKS={'/etc/systemd/system/default.target':'/usr/lib/systemd/system/graphical.target',
       '/etc/systemd/system/display-manager.service':'/usr/lib/systemd/system/gdm.service'}
DB_DIRS={'','info','updates','parts','alternatives','triggers','methods','methods/file','methods/ftp','methods/mnt','methods/media'}
DB_FILES={'status','status-old','lock','lock-frontend','triggers/Lock','triggers/Unincorp'}


def snapshot(root):
    root=Path(root);result={};device=root.stat().st_dev
    if root.resolve()!=root or not root.is_dir():raise ValueError('Candidate root redirects')
    p=payload_module()
    for base,directories,files in os.walk(root,followlinks=False):
        for name in sorted(directories+files):
            path=Path(base)/name;info=path.lstat();virtual='/'+path.relative_to(root).as_posix()
            if info.st_dev!=device or os.listxattr(path,follow_symlinks=False):raise ValueError('Candidate cross-device/xattr output')
            row={'mode':info.st_mode,'uid':info.st_uid,'gid':info.st_gid}
            if stat.S_ISREG(info.st_mode):row['sha256']=p.digest(path)
            elif stat.S_ISLNK(info.st_mode):row['symlink']=os.readlink(path)
            elif stat.S_ISDIR(info.st_mode):row['directory']=True
            else:raise ValueError('Candidate special-node output')
            result[virtual]=row
    return result


def account_entries(policy):
    return {'/'+path:{'mode':stat.S_IFREG|mode,'uid':0,'gid':0,'sha256':hashlib.sha256(data).hexdigest()}
            for path,(data,mode) in account_files(policy['accounts']).items()}


def candidate_entries(actual,manifest,policy):
    """Closed source origin classification; unknown output stays a blocker."""
    owned=manifest['ownership']['entries'];fresh={'/'+name:row for name,row in manifest['ownership']['fresh_directories'].items()}
    accounts=account_entries(policy);generated={};blockers=[]
    packages={row['name'] for row in manifest['components']}
    for path,row in actual.items():
        if path in owned:
            if row!=owned[path]:blockers.append({'path':path,'reason':'owned-output-differs-requires-native-record-requalification'})
            continue
        origin=None
        if path in fresh and row==fresh[path]:origin='fresh-system-accounts'
        elif path in accounts and row==accounts[path]:origin='fresh-system-accounts'
        elif path in LINKS and row=={'mode':stat.S_IFLNK|0o777,'uid':0,'gid':0,'symlink':LINKS[path]}:origin='pam-service-policy'
        elif path=='/lost+found' and row=={'mode':stat.S_IFDIR|0o700,'uid':0,'gid':0,'directory':True}:origin='fresh-filesystem'
        elif path=='/etc/ld.so.cache' and row.get('mode')==stat.S_IFREG|0o644 and row.get('uid')==row.get('gid')==0:origin='generated-caches'
        elif path=='/var/cache/ldconfig' and row=={'mode':stat.S_IFDIR|0o700,'uid':0,'gid':0,'directory':True}:origin='generated-caches'
        elif path=='/var/lib/dpkg' or path.startswith('/var/lib/dpkg/'):
            relative=path.removeprefix('/var/lib/dpkg').lstrip('/')
            legal=relative in DB_DIRS if row.get('directory') else relative in DB_FILES
            if not legal and relative.startswith('info/') and relative.count('/')==1:
                match=re.fullmatch(r'([a-z0-9][a-z0-9+.-]*)(?::(?:amd64|all))?\.(list|md5sums|conffiles|shlibs|symbols)',relative[5:])
                legal=bool(match and match[1] in packages)
            if legal and row.get('uid')==row.get('gid')==0 and (row.get('mode')==stat.S_IFDIR|0o755 if row.get('directory') else row.get('mode') in {stat.S_IFREG|0o644,stat.S_IFREG|0o640,stat.S_IFREG|0o600}):origin='native-dpkg-database'
        if origin:generated[path]={**row,'origin':origin}
        else:blockers.append({'path':path,'reason':'unattributed-or-unexpected-generated-output'})
    for missing in sorted(set(owned)-set(actual)):blockers.append({'path':missing,'reason':'selected-owned-path-missing'})
    return generated,blockers


def resource_plan(manifest):
    p=payload_module();entries=manifest['ownership']['entries'];plan=[]
    for virtual,binding in sorted(manifest['generated']['owned_cache_bindings'].items()):
        p.canonical(virtual);tool=binding['tool'];p.canonical(tool['path'])
        if entries.get(tool['path'],{}).get('sha256')!=tool['sha256'] or entries.get(virtual,{}).get('sha256')!=binding['output_sha256']:
            raise ValueError('Candidate producer/output lacks selected ownership')
        namespace=p.cache_namespace(virtual,entries)
        if hashlib.sha256(p.encoded(namespace)).hexdigest()!=binding['input_namespace_sha256'] or binding['inputs']!={key:row['sha256'] for key,row in namespace.items() if 'sha256' in row}:
            raise ValueError('Candidate cache union differs from selected namespace')
        plan.append({'output':virtual,'tool':tool,'argv':cache_command(virtual,tool['path']),
                     'input_namespace_sha256':binding['input_namespace_sha256']})
    return plan


def save(path,value):
    p=payload_module()
    with Path(path).open('xb') as stream:
        os.fchmod(stream.fileno(),0o600);stream.write(p.encoded(value));stream.flush();os.fsync(stream.fileno())


def qualify(assembly,manifest,policy,system):
    """Run only fixed native producers in generation1; preserve every failure."""
    system.require_root();assembly.recheck();p=payload_module()
    root=Path(assembly.root);work=Path(assembly.work)
    if root!=work/'root' or root.resolve()!=root or work.resolve()!=work or not root.is_relative_to('/sources/stage'):
        raise ValueError('Resource qualification requires fixed native source assembly')
    outputs=('resource-intent.json','candidate-generated-entries.json','candidate-clean-image-manifest.json','candidate-resource-receipt.json')
    if any(os.path.lexists(work/name) for name in outputs):raise ValueError('Preserve prior/uncertain resource generation')
    validate_policy(policy,manifest)
    plan=resource_plan(manifest)
    before=snapshot(root)
    # No inherited account/home/private state may become the candidate baseline.
    files=account_files(policy['accounts'])
    if any('/'+path in before for path in files):raise ValueError('Fresh candidate account files already exist')
    for relative in ('home','root','run'):
        directory=root/relative
        if directory.is_symlink() or directory.exists() and any(directory.iterdir()):raise ValueError('Candidate inherited private/runtime state')
    _,initial_blockers=candidate_entries(before,manifest,policy)
    if initial_blockers:raise ValueError('Unpacked candidate does not match selected ownership/database policy')
    intent={'version':1,'kind':'unqualified-native-resource-candidate','manifest_sha256':hashlib.sha256(p.encoded(manifest)).hexdigest(),
            'policy_sha256':hashlib.sha256(p.encoded(policy)).hexdigest(),'source_sha256':p.digest(__file__),
            'root_inode':root.stat().st_ino,'root_device':root.stat().st_dev,'production_ready':False}
    save(work/'resource-intent.json',intent)
    commands=[];loader=None
    try:
        for relative,row in sorted(manifest['ownership']['fresh_directories'].items(),key=lambda item:(item[0].count('/'),item[0])):
            p.canonical('/'+relative);path=root/relative
            if path.parent.resolve()!=path.parent:raise ValueError('Fresh candidate parent redirects')
            path.mkdir(mode=stat.S_IMODE(row['mode']),exist_ok=True)
            info=path.lstat()
            if not stat.S_ISDIR(info.st_mode) or info.st_uid or info.st_gid:raise ValueError('Fresh candidate directory identity')
            path.chmod(stat.S_IMODE(row['mode']))
        for relative,(data,mode) in files.items():regular(root,relative,data,mode)
        lost=root/'lost+found'
        if not lost.exists():lost.mkdir(mode=0o700)
        elif lost.is_symlink() or not lost.is_dir() or any(lost.iterdir()):raise ValueError('Candidate lost+found is not fresh')
        for virtual,target in LINKS.items():
            if not manifest['ownership']['entries'].get(target,{}).get('sha256'):raise ValueError('Candidate GDM target lacks selected ownership')
            path=root/virtual.lstrip('/')
            if path.parent.resolve()!=path.parent:raise ValueError('Candidate service parent redirects')
            if path.exists() or path.is_symlink():
                if not path.is_symlink() or os.readlink(path)!=target:raise ValueError('Candidate service link conflicts')
            else:os.symlink(target,path)
        seen=set();cache_results={}
        for recipe in plan:
            virtual=recipe['output'];binding=manifest['generated']['owned_cache_bindings'][virtual]
            tool=recipe['tool'];source=root/tool['path'].lstrip('/')
            if source.is_symlink() or source.parent.resolve()!=source.parent or p.digest(source)!=tool['sha256']:raise ValueError('Candidate resource tool changed')
            command=recipe['argv']
            if tuple(command) not in seen:
                system.run(['/usr/bin/chroot',str(root),*command],timeout=120);commands.append(command);seen.add(tuple(command));assembly.recheck()
            path=root/virtual.lstrip('/')
            if path.is_symlink() or not path.is_file():raise ValueError('Candidate resource output missing')
            cache_results[virtual]={'recorded_sha256':binding['output_sha256'],'actual_sha256':p.digest(path),
                'tool':tool,'input_namespace_sha256':binding['input_namespace_sha256']}
        actual=snapshot(root);generated,blockers=candidate_entries(actual,manifest,policy)
        if not blockers:
            loader=generate_loader_cache(root,manifest['ownership']['entries'],system);assembly.recheck()
            actual=snapshot(root);generated,blockers=candidate_entries(actual,manifest,policy)
        # Unknown paths/owned output drift are explicit blockers, never an
        # override added to generated entries. Even zero blockers needs review.
        save(work/'candidate-generated-entries.json',generated)
        save(work/'candidate-clean-image-manifest.json',actual)
        receipt={**intent,'state':'blocked-native-output-review' if blockers else 'native-candidate-awaiting-independent-review',
            'commands':commands,'cache_results':cache_results,'loader':loader,'blockers':blockers,
            'generated_entries_sha256':p.digest(work/'candidate-generated-entries.json'),
            'candidate_image_manifest_sha256':p.digest(work/'candidate-clean-image-manifest.json'),
            'native_boot_verified':False,'finalizer_qualified':False,'next':'Independent review, then NEW generation2 unpack and real NativeFinalizer; never rerun candidate1.'}
        save(work/'candidate-resource-receipt.json',receipt);assembly.recheck();return receipt
    except BaseException:
        # Intent/root/tool effects remain intact. No success-shaped report is
        # synthesized and an uncertain generation cannot be replayed.
        raise

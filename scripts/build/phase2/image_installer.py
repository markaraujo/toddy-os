#!/usr/bin/env python3
"""Fixed MVP seal/embed bridge; real installer qualification is never synthesized."""
import hashlib,json,os,shutil,stat,sys
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
sys.path[:0]=[str(HERE),str(ROOT),str(HERE.parent/'h10')]
import offline_payload as p
from image_assemble import native_guard,write,private_directory
from copy_selected_root import snapshot,tree_names
from runtime.installer.linux_disk import LinuxDisk
from runtime.installer.composition import Composition,secured
from seal_installer_composition import seal
STAGE=Path('/sources/stage')
INPUTS=STAGE/'toddy-mvp-installer-native-inputs'
OFFLINE=STAGE/'toddy-mvp-offline-image-2/mvp-offline-root-2'
SEALED=STAGE/'toddy-mvp-installer-composition-1'
WORK=STAGE/'toddy-mvp-live-image-2';IMAGE=WORK/'mvp-live-root-2'
PREFIX='usr/share/toddy/installer/composition'
CLASS='phase2-mvp-preinstalled-v1'

def sealed_source(base):
    # Source-only coordinator constructs custody at one fixed staging path.
    # Production Composition() still accepts no path or bypass argument.
    value=object.__new__(Composition);value.base=base;value.bundle=base/'payload'
    ready=value.readiness()
    if value.manifest.get('delivery_class')!=CLASS or value.manifest.get('g2_eligible') is not False:raise ValueError('Only typed non-G2 MVP composition may enter MVP media')
    return value,ready

def native_seal():
    result=seal(OFFLINE,INPUTS,SEALED)
    value,ready=sealed_source(SEALED)
    return dict(result,delivery_class=CLASS,g2_eligible=False,supported_firmware=ready['supported_firmware'])

def additive_delta(before,after,source):
    """Only the source-exact new tree plus parent directory mtime may change."""
    expected={PREFIX if name=='.' else PREFIX+'/'+name:row for name,row in source['entries'].items()}
    if any(row.get('xattrs') for row in source['entries'].values()) or source['hardlink_groups']:raise ValueError('Sealed input metadata must be regular no-xattr single-link custody')
    if set(after['entries'])!=set(before['entries'])|set(expected):raise ValueError('Installer embedding changed namespace outside exact tree')
    if any(after['entries'].get(name)!=row for name,row in expected.items()):raise ValueError('Embedded installer source metadata/bytes differ')
    parent=str(Path(PREFIX).parent)
    for name,row in before['entries'].items():
        actual=after['entries'][name]
        if name==parent:
            row={key:value for key,value in row.items() if key!='mtime_ns'}
            actual={key:value for key,value in actual.items() if key!='mtime_ns'}
        if actual!=row:raise ValueError('Installer embedding modified existing image path: '+name)
    if after['hardlink_groups']!=before['hardlink_groups']:raise ValueError('Installer embedding changed existing hardlinks')
    return expected

def embed():
    private_directory(WORK,0o700);private_directory(IMAGE,0o755)
    journal_path=secured(WORK/'evidence/assembly.json');journal=p.strict(journal_path.read_bytes())
    external=lambda path:Path('/mnt/lfs')/path.relative_to('/')
    assembler=HERE/'image_assemble.py'
    if (journal.get('assembled') is not True or journal.get('delivery_class')!=CLASS or journal.get('g2_eligible') is not False or
        journal.get('image')!=str(external(IMAGE)) or journal.get('evidence')!=str(external(WORK/'evidence')) or journal.get('assembler_sha256')!=p.digest(assembler)):
        raise ValueError('Actual complete MVP desktop assembly required before embedding')
    manifest=secured(WORK/'evidence/image-manifest.json');before=snapshot(IMAGE,tree_names(IMAGE))
    if before!=p.strict(manifest.read_bytes()):raise ValueError('MVP desktop root changed since actual snapshot')
    value,ready=sealed_source(SEALED);source=snapshot(SEALED,tree_names(SEALED));destination=IMAGE/PREFIX
    target=WORK/'evidence-installer';intent=WORK/'installer-embed-intent.json'
    if any(os.path.lexists(path) for path in (target,intent,destination)):raise ValueError('Preserve existing or uncertain installer embedding; no replay')
    if not destination.parent.is_dir() or destination.parent.resolve()!=destination.parent:raise ValueError('Installer image parent is not source-owned canonical directory')
    if source['hardlink_groups']:raise ValueError('Sealed input has external hardlink custody')
    for name,row in source['entries'].items():
        if row['mode']&0o022:raise ValueError('Sealed input has writable metadata')
        if not stat.S_ISDIR(row['mode']):secured(SEALED/name,limit=8*1024**3)
        if row['uid'] or row['gid'] or row['xattrs'] or not (stat.S_ISDIR(row['mode']) or stat.S_ISREG(row['mode'])):raise ValueError('Sealed composition has unqualified metadata')
    bound=p.file_tree_storage_bound({name:row['size'] for name,row in source['entries'].items() if 'size' in row},os.statvfs(STAGE).f_frsize)
    p.require_capacity(STAGE,bound+512*1024**2)
    write(intent,{'version':1,'state':'sealed-installer-embed-intended','source_composition_sha256':p.digest(secured(SEALED/'composition.json')),
        'desktop_journal_sha256':p.digest(journal_path),'desktop_manifest_sha256':p.digest(manifest),'producer_sha256':p.digest(Path(__file__)),'copy_bound_bytes':bound})
    shutil.copytree(SEALED,destination,copy_function=shutil.copy2)
    for base,dirs,files in os.walk(destination,topdown=False):
        for name in files:
            fd=os.open(Path(base)/name,os.O_RDONLY|os.O_NOFOLLOW)
            try:os.fsync(fd)
            finally:os.close(fd)
        fd=os.open(base,os.O_DIRECTORY|os.O_NOFOLLOW)
        try:os.fsync(fd)
        finally:os.close(fd)
    value.recheck()
    if snapshot(SEALED,tree_names(SEALED))!=source:raise ValueError('Sealed source changed during embedding')
    copied,copied_ready=sealed_source(destination)
    if copied_ready!=ready:raise ValueError('Embedded production readiness differs')
    after=snapshot(IMAGE,tree_names(IMAGE));added=additive_delta(before,after,source)
    # New files have no ACLs and their source-owned parent has no default ACL;
    # thus the existing exact ACL sidecar still covers all extended ACL paths.
    for name in added:
        if after['entries'][name]['xattrs']:raise ValueError('Embedded input unexpectedly adds ACL/xattr state')
    target.mkdir(mode=0o700);write(target/'image-manifest.json',after)
    receipt={'version':1,'state':'actual-sealed-mvp-installer-embedded','delivery_class':CLASS,'g2_eligible':False,
        'source_composition_sha256':p.digest(SEALED/'composition.json'),'embedded_composition_sha256':p.digest(destination/'composition.json'),
        'readiness':ready,'added_paths':sorted(added),'source_snapshot_sha256':hashlib.sha256(p.encoded(source)).hexdigest(),
        'native_boot_verified_by_this_copy':False,'producer_sha256':p.digest(Path(__file__))}
    write(target/'installer-embedded.json',receipt)
    journal.update(evidence=str(external(target)),installer_ready=True,installer_supported_firmware=ready['supported_firmware'],
        installer_composition_sha256=receipt['embedded_composition_sha256'],installer_embed_receipt_sha256=p.digest(target/'installer-embedded.json'),
        actions=[{'step':'image-manifest','finished':True,'report':'image-manifest.json','sha256':p.digest(target/'image-manifest.json')}])
    write(target/'assembly.json',journal)
    for directory in (target,WORK):
        fd=os.open(directory,os.O_DIRECTORY|os.O_NOFOLLOW)
        try:os.fsync(fd)
        finally:os.close(fd)
    return dict(receipt,journal=str(external(target/'assembly.json')))

def main():
    if sys.argv[1:] not in (['seal'],['embed']) or Path(__file__).resolve()!=Path('/opt/toddy-build/scripts/build/phase2/image_installer.py'):raise ValueError('Fixed MVP installer coordinator command required')
    os.umask(0o077);native_guard(LinuxDisk())
    # Outer image_native owns the global lease; no independent unsafe entry.
    actual=os.fstat(9)
    if (not stat.S_ISREG(actual.st_mode) or actual.st_uid or actual.st_gid or actual.st_mode&0o022 or actual.st_nlink!=1 or
            not __import__('re').search(r'^lock:.*\bFLOCK\b.*\bWRITE\b',Path('/proc/self/fdinfo/9').read_text(),__import__('re').M)):
        raise ValueError('Inherited exclusive image lease required')
    # Outer image_native validates canonical builder lock inode before chroot.
    # Its /var/log path is outside this native root; do not compare against a
    # different target-local file or reopen/reacquire the builder lease.
    print(json.dumps(native_seal() if sys.argv[1]=='seal' else embed(),sort_keys=True))

if __name__=='__main__':main()

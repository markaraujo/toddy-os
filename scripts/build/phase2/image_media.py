"""Fixed B12 native compression/initramfs/ISO phases over a qualified image journal.

No historical milestone CLI is rerun and no boot/release acceptance is inferred.
Missing real assembly attribution fails before creating a media generation.
"""
import fcntl
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path[:0]=[str(HERE),str(HERE.parent/'h11'),str(HERE.parent/'h10'),str(HERE.parent)]
import offline_payload as p
import assemble_iso
import hybrid_media
import initramfs_archive
import initramfs_input
from compress_root import compress,atomic_json
from copy_selected_root import snapshot,tree_names
from package_backend import PackageBackend

TARGET=Path('/mnt/lfs')
STAGE=TARGET/'sources/stage'
IMAGE=STAGE/'toddy-live-image-2/live-root-2'
JOURNAL=STAGE/'toddy-live-image-2/evidence/assembly.json'
COMPRESSION=STAGE/'toddy-live-compression-1'
INITRAMFS=STAGE/'toddy-live-initramfs-1'
MEDIA=STAGE/'toddy-release-media-1'
PROJECTION=STAGE/'toddy-image-projection-1/live-projection.json'
ASSEMBLER=HERE/'image_assemble.py'
BUILD=Path('/var/log/toddy/build')
RECORDS=Path('/var/log/toddy/packages')
TOOLS={'linux-kernel','grub','mtools','libburn','libisofs','libisoburn','squashfs-tools'}
EPOCH=1794787200  # 2026-11-16 00:00:00 UTC, explicit source recipe timestamp.
RESERVE=16*1024**3


def capacity(parent,extra):
    free=os.statvfs(parent)
    if free.f_bavail*free.f_frsize < RESERVE+extra:
        raise ValueError('Media phase requires16GiB reserve plus complete output/readback capacity')


def native_tools(backend):
    projection=p.strict(initramfs_input.physical(TARGET,PROJECTION).read_bytes())
    rows={row['name']:row for row in projection['components']}
    if not TOOLS<=rows.keys():raise ValueError('Native media tools missing from live projection')
    versions={name:rows[name]['version'] for name in sorted(TOOLS)}
    evidence,files=assemble_iso.packages(backend,versions)
    for name,observed in evidence.items():
        row=rows[name]
        if observed['record_sha256']!=row['component_record_sha256'] or observed['archive_sha256']!=row['archive_sha256']:
            raise ValueError('Native media tools differ from frozen current projection')
    return versions,evidence,files


def assembly_input():
    journal=p.strict(initramfs_input.physical(TARGET,JOURNAL).read_bytes())
    if (journal.get('assembled') is not True or journal.get('release_profile') is not True or
            journal.get('image')!=str(IMAGE) or journal.get('evidence')!=str(JOURNAL.parent) or
            journal.get('assembler_sha256')!=p.digest(ASSEMBLER)):
        raise ValueError('Real current B12 final assembly journal required')
    actions=[row for row in journal['actions'] if row['step']=='image-manifest']
    if len(actions)!=1 or actions[0].get('finished') is not True or Path(actions[0]['report']).name!=actions[0]['report']:
        raise ValueError('Final assembly manifest action missing')
    manifest=initramfs_input.physical(TARGET,JOURNAL.parent/actions[0]['report'])
    if p.digest(manifest)!=actions[0]['sha256']:raise ValueError('Final assembly manifest changed')
    expected=p.strict(manifest.read_bytes())
    if snapshot(IMAGE,tree_names(IMAGE))!=expected:raise ValueError('Actual image differs from final assembly')
    return journal,manifest,expected


def compression_phase(backend):
    journal,manifest,expected=assembly_input()
    _,evidence,files=native_tools(backend)
    size=sum(row.get('size',0) for row in expected['entries'].values())
    capacity(STAGE,2*size+2*1024**3)
    tools={'accepted_package':True,'archive_sha256':evidence['squashfs-tools']['archive_sha256'],
        'binaries':{name:{'path':str(TARGET/'usr/bin'/name),'sha256':files['/usr/bin/'+name]}
                    for name in ('mksquashfs','unsquashfs')}}
    initial=p.digest(JOURNAL);manifest_sha=p.digest(manifest)
    report=compress(backend,IMAGE,COMPRESSION,expected,tools,EPOCH)
    if p.digest(JOURNAL)!=initial or p.digest(manifest)!=manifest_sha:
        raise ValueError('Assembly changed during compression')
    report['assembly_binding']={'journal':str(JOURNAL),'journal_sha256':initial,
        'manifest':str(manifest),'manifest_sha256':p.digest(manifest),'release_profile':True}
    atomic_json(COMPRESSION/'compression.json',report)
    return report


def live_identity():
    # The live account/session policy embeds media identity before compression.
    # Never derive it from SquashFS/final-image bytes (that would be recursive).
    import live_profile
    path=initramfs_input.physical(TARGET,IMAGE/'usr/share/toddy/live-image.json')
    value=p.strict(path.read_bytes())
    required={'version','image_class','live_uid','live_user','media_id','producer_sha256','unit_sha256','profile_source_sha256'}
    if (set(value)!=required or value['version']!=1 or type(value['version']) is not int or
            value['image_class']!='phase2-live-installer' or value['live_uid']!=1000 or
            type(value['live_uid']) is not int or value['live_user']!='toddy-live'):
        raise ValueError('Exact source-attributed live image class required')
    source=initramfs_input.physical(TARGET,IMAGE/'usr/lib/toddy/installer/live_session.py')
    unit=initramfs_input.physical(TARGET,IMAGE/'etc/systemd/system/toddy-live-owner.service')
    if (value['producer_sha256']!=p.digest(source) or value['unit_sha256']!=p.digest(unit) or
            value['profile_source_sha256']!=p.digest(HERE/'live_profile.py')):
        raise ValueError('Live image class source/unit custody differs')
    inputs=STAGE/'toddy-live-native-inputs'
    manifest=initramfs_input.physical(TARGET,inputs/'payload/manifest.json')
    policy=initramfs_input.physical(TARGET,inputs/'policy.json')
    expected=live_profile.media_identity(p.digest(manifest),p.digest(policy))
    if not re.fullmatch('[0-9a-f]{64}',value['media_id']) or value['media_id']!=expected:
        raise ValueError('Live image media identity differs from selected payload/policy')
    return expected


def initramfs_phase(backend):
    native_tools(backend)
    binding=initramfs_input.verify(TARGET,COMPRESSION/'compression.json',True,assembler=ASSEMBLER)
    capacity(STAGE,1024**3)
    media_id=live_identity()
    scripts=HERE.parent/'h10'
    report=initramfs_archive.assemble(TARGET,INITRAMFS,RECORDS,scripts/'live_init.sh',
        scripts/'live_media.sh',media_id,binding['rootfs_sha256'],binding['epoch'])
    initramfs_input.unchanged(TARGET,binding)
    report['compression_binding']=binding
    atomic_json(INITRAMFS/'manifest.json',report)
    return report


def archive_input():
    path=initramfs_input.physical(TARGET,INITRAMFS/'manifest.json')
    report=p.strict(path.read_bytes());recorded=report.get('compression_binding',{})
    binding=initramfs_input.verify(TARGET,COMPRESSION/'compression.json',True,assembler=ASSEMBLER)
    if recorded!=binding or report.get('rootfs_sha256')!=binding['rootfs_sha256'] or report.get('epoch')!=binding['epoch']:
        raise ValueError('Initramfs does not bind current native root generation')
    media_id=report.get('media_id','')
    if not re.fullmatch('[0-9a-f]{64}',media_id) or media_id!=live_identity():raise ValueError('Media identity')
    archive=initramfs_input.physical(TARGET,INITRAMFS/'initramfs.cpio.gz')
    if archive.stat().st_size!=report['gzip_bytes'] or p.digest(archive)!=report['gzip_sha256']:
        raise ValueError('Initramfs gzip custody')
    with gzip.open(archive,'rb') as stream:raw=stream.read(256*1024**2+1)
    if len(raw)>256*1024**2 or hashlib.sha256(raw).hexdigest()!=report['cpio_sha256']:
        raise ValueError('Initramfs bounded raw custody')
    if initramfs_archive.validate_newc(raw,report['entries'],binding['epoch'])!=report['entry_count']:
        raise ValueError('Initramfs entry inventory')
    scripts=HERE.parent/'h10'
    public={'etc/toddy-live/media-id':(media_id+'\n').encode(),
        'etc/toddy-live/rootfs.sha256':(binding['rootfs_sha256']+'\n').encode(),
        'init':(scripts/'live_init.sh').read_bytes(),
        'usr/lib/toddy/live_media.sh':(scripts/'live_media.sh').read_bytes(),
        'usr/lib/toddy/restore_live_acls.sh':(scripts/'restore_live_acls.sh').read_bytes()}
    if any(report['entries'][name]['body_sha256']!=hashlib.sha256(data).hexdigest() for name,data in public.items()):
        raise ValueError('Initramfs fixed reviewed scripts differ')
    return report,binding,{str(path):p.digest(path),str(archive):p.digest(archive)}


def iso_phase(backend):
    versions,evidence,files=native_tools(backend)
    report,binding,init_evidence=archive_input()
    kernel=initramfs_input.physical(TARGET,IMAGE/'boot/vmlinuz-7.1.8-toddy')
    if p.digest(kernel)!=files['/boot/vmlinuz-7.1.8-toddy']:
        raise ValueError('Image kernel differs from projected source-owned kernel')
    inputs={'boot/vmlinuz-7.1.8-toddy':kernel,
        'boot/initramfs.cpio.gz':INITRAMFS/'initramfs.cpio.gz',
        'live/rootfs.squashfs':Path(binding['artifact'])}
    hashes={name:p.digest(path) for name,path in inputs.items()}
    if os.path.lexists(MEDIA):raise ValueError('Preserve existing/uncertain media generation')
    capacity(STAGE,3*sum(path.stat().st_size for path in inputs.values())+2*1024**3)
    MEDIA.mkdir(mode=0o700)
    result={'complete':False,'native_kernel_boot_verified':False,'release_accepted':False,
        'physical_hardware_tested':False,'producer_sha256':p.digest(Path(__file__)),
        'compression_binding':binding,'native_packages':evidence,'stages':[]}
    atomic_json(MEDIA/'result.json',result)
    source=MEDIA/'input'
    for name,path in inputs.items():
        destination=source/name;destination.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(path,destination);destination.chmod(0o644)
        if p.digest(destination)!=hashes[name]:raise ValueError('Media copy changed')
    (source/'boot/grub').mkdir();(source/'.toddy').mkdir()
    (source/'.toddy'/report['media_id']).touch()
    (source/'boot/grub/grub.cfg').write_text(hybrid_media.live_configuration())
    def stage(name,argv):
        entry={'name':name,'argv':argv,'exit':None};result['stages'].append(entry)
        atomic_json(MEDIA/'result.json',result)
        with (MEDIA/(name+'.log')).open('xb') as log:
            completed=subprocess.run(['/usr/sbin/chroot',str(TARGET),'/usr/bin/env','-i',
                'HOME=/'+MEDIA.relative_to(TARGET).as_posix(),'PATH=/usr/bin:/usr/sbin','LC_ALL=C.UTF-8',
                'MTOOLSRC=/dev/null','/usr/bin/timeout','--kill-after=60','1800',*argv],stdout=log,stderr=subprocess.STDOUT,check=False)
            log.flush();os.fsync(log.fileno())
        entry.update(exit=completed.returncode,log_sha256=p.digest(MEDIA/(name+'.log')))
        atomic_json(MEDIA/'result.json',result);completed.check_returncode()
    media=hybrid_media.compose(TARGET,MEDIA,stage,marker='/.toddy/'+report['media_id'])
    initramfs_input.unchanged(TARGET,binding)
    if (any(p.digest(Path(name))!=sha for name,sha in init_evidence.items()) or
            any(p.digest(path)!=hashes[name] for name,path in inputs.items()) or
            assemble_iso.packages(backend,versions)!=(evidence,files)):
        raise ValueError('Media native input changed')
    with (MEDIA/'SHA256SUMS').open('x') as stream:
        stream.write(media['sha256']+'  toddy.iso\n');stream.flush();os.fsync(stream.fileno())
    result.update(complete=True,media=media,pending=['actual BIOS/UEFI live and blank-disk installer qualification','final source/license/privacy audit','physical owner testing'])
    atomic_json(MEDIA/'result.json',result)
    return result


def main():
    if (sys.argv[1:] not in (['compress'],['initramfs'],['iso']) or os.getuid()!=0 or os.geteuid()!=0 or
            Path(__file__).resolve()!=Path('/opt/toddy-build/scripts/build/phase2/image_media.py')):
        raise ValueError('Fixed root coordinator media command required')
    os.umask(0o077)
    subprocess.run(['/usr/bin/bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
    with (BUILD/'build.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if list(BUILD.glob('*.running.json')) or (BUILD/'input-sync.running').exists():raise ValueError('Preserve active native operation')
        backend=PackageBackend()
        if not backend.native:raise ValueError('Accepted native backend required')
        initramfs_input.physical(TARGET,STAGE,directory=True)
        result={'compress':compression_phase,'initramfs':initramfs_phase,'iso':iso_phase}[sys.argv[1]](backend)
        print(json.dumps(result,sort_keys=True))


if __name__=='__main__':main()

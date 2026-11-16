"""Preserve actual completed-install evidence before the qualification VM stops.

Source-only root operator tool. It never installs, mounts, boots, retries an
operation, or fabricates detached boot/login/recovery qualification.
"""
import argparse
import fcntl
import hashlib
import os
from pathlib import Path
import re
import sqlite3
import sys

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[3]
sys.path[:0]=[str(ROOT),str(Path(__file__).resolve().parent)]
from installer_qualification import NativeInputs,INPUTS,JOURNAL
from runtime.installer.composition import secured,validate_finalizer_report
from runtime.installer.disk_plan import InstallError,QualificationPolicy,validate_plan
from runtime.installer.installed_boot import RELEASE
from runtime.installer.linux_disk import LinuxDisk
from runtime.installer.native_finalizer import payload_module

REPORTS=Path('/run/toddy-installer')


def read_review(path):
    p=payload_module();value=p.strict(secured(path,limit=65536).read_bytes())
    if (not isinstance(value,dict) or set(value)!={'state','disk_writes','plan'} or
            value['state']!='qualification-review-only' or value['disk_writes'] is not False):
        raise InstallError('installer_collect_actual_review_required')
    return validate_plan(value['plan'])


def read_operation(plan):
    """Read only the complete journal; never construct writable Journal()."""
    p=payload_module();database=secured(JOURNAL/'operations.sqlite')
    connection=sqlite3.connect('file:'+str(database)+'?mode=ro',uri=True,isolation_level=None)
    try:
        connection.execute('BEGIN')
        row=connection.execute('SELECT plan_sha256,state,step FROM operations WHERE id=?',
            (plan['options']['operation_id'],)).fetchone()
        if row!=(plan['plan_sha256'],'completed','complete'):
            raise InstallError('installer_collect_completed_exact_operation_required')
        result={}
        for name in ('filesystems','boot','grub'):
            body=connection.execute('SELECT body FROM receipts WHERE operation_id=? AND step=?',
                (plan['options']['operation_id'],name)).fetchone()
            if body is None or not isinstance(body[0],str) or len(body[0].encode())>65536:
                raise InstallError('installer_collect_native_receipt_missing')
            result[name]=p.strict(body[0].encode())
        return result
    finally:connection.close()


def private_directory(path):
    import stat
    info=path.lstat()
    if path.resolve()!=path or not stat.S_ISDIR(info.st_mode) or info.st_uid or info.st_gid or info.st_mode&0o077:
        raise InstallError('installer_collect_private_directory')


def write_new(path,data):
    if os.path.lexists(path):
        if secured(path).read_bytes()!=data:raise InstallError('installer_collect_existing_evidence_differs')
        return
    partial=path.with_suffix(path.suffix+'.part')
    with partial.open('xb') as stream:
        os.fchmod(stream.fileno(),0o400);stream.write(data);stream.flush();os.fsync(stream.fileno())
    if os.path.lexists(path):raise InstallError('installer_collect_output_race')
    os.rename(partial,path)
    directory=os.open(path.parent,os.O_DIRECTORY)
    try:os.fsync(directory)
    finally:os.close(directory)


def collect(plan,inputs,system):
    p=payload_module();plan=validate_plan(plan);system.require_root();inputs.recheck()
    manifest=inputs.manifest;descriptor=inputs.descriptor
    expected_payload={'sha256':descriptor['payload_manifest_sha256'],'catalog_sha256':manifest['catalog_sha256'],'bytes':manifest['bytes']}
    if plan['payload']!=expected_payload:raise InstallError('installer_collect_input_binding')
    policy=QualificationPolicy(plan['target']['serial']);policy.check(plan['target'])
    # Read the existing writer lock, no new lock/database/operation is created.
    writer=secured(JOURNAL/'writer.lock');lock=os.open(writer,os.O_RDONLY|os.O_NOFOLLOW)
    try:
        fcntl.flock(lock,fcntl.LOCK_SH|fcntl.LOCK_NB)
        native=read_operation(plan)
        disk=system.probe(plan['target']['path'],require_blank=False);policy.check(disk)
        if any(disk[key]!=value for key,value in plan['target'].items() if key!='blank'):
            raise InstallError('installer_collect_target_changed_or_mounted')
        boot=native['boot'];filesystems=native['filesystems'];grub=native['grub']
        if (not isinstance(boot,dict) or set(boot)!={'verified','kernel','initramfs','kernel_sha256','initramfs_sha256'} or
                boot['verified'] is not True or boot['kernel']!='vmlinuz-'+RELEASE or
                boot['initramfs']!='initramfs-'+RELEASE+'-installed.img' or
                boot['kernel_sha256']!=inputs.boot['kernel_sha256'] or not isinstance(boot['initramfs_sha256'],str) or not re.fullmatch('[0-9a-f]{64}',boot['initramfs_sha256'])):
            raise InstallError('installer_collect_actual_installed_boot_receipt')
        if (not isinstance(filesystems,dict) or set(filesystems)!={'root_uuid','esp_uuid'} or
                not isinstance(filesystems['root_uuid'],str) or not re.fullmatch('[A-Fa-f0-9-]{4,40}',filesystems['root_uuid']) or
                (plan['options']['boot_mode']=='bios' and filesystems['esp_uuid'] is not None) or
                (plan['options']['boot_mode']=='uefi' and not isinstance(filesystems['esp_uuid'],str))):
            raise InstallError('installer_collect_actual_filesystem_receipt')
        if (not isinstance(grub,dict) or grub.get('verified') is not True or grub.get('config_path')!='/etc/toddy/grub.cfg' or
                grub.get('boot_link')!='../../etc/toddy/grub.cfg' or not isinstance(grub.get('config_sha256'),str) or not re.fullmatch('[0-9a-f]{64}',grub['config_sha256'])):
            raise InstallError('installer_collect_actual_grub_receipt')
        source=REPORTS/('finalization-target-'+plan['options']['operation_id'])
        reports={};hashes={}
        for name in sorted(p.CHECKS):
            data=secured(source/(name+'.json')).read_bytes()
            validate_finalizer_report(p.strict(data),name,descriptor)
            reports[name]=data;hashes[name]=hashlib.sha256(data).hexdigest()
        sources={name.removeprefix('source:'):sha for name,sha in inputs.pins.items() if name.startswith('source:')}
        if 'installed_boot.py' not in sources:raise InstallError('installer_collect_source_closure_missing')
        handoff={'version':1,'kind':'native-installed-disk-handoff-v1','state':'completed-install-detached-boots-pending',
            'operation_id':plan['options']['operation_id'],'plan_sha256':plan['plan_sha256'],
            'firmware':plan['options']['boot_mode'],'target_serial':disk['serial'],'root_uuid':filesystems['root_uuid'],
            'esp_uuid':filesystems['esp_uuid'],'expected_owner':{key:plan['options'][key] for key in ('username','uid','gid')},
            'input_manifest_sha256':descriptor['payload_manifest_sha256'],'image_manifest_sha256':descriptor['image_manifest_sha256'],
            'kernel_sha256':boot['kernel_sha256'],'initramfs_sha256':boot['initramfs_sha256'],
            'initramfs_source_sha256':sources['installed_boot.py'],'grub_config_sha256':grub['config_sha256'],
            'source_sha256':sources,'finalizer_reports_sha256':hashes,'payload_storage':manifest.get('storage'),
            'producer_sha256':p.digest(Path(__file__)),'detached_boots_collected':0,
            'fresh_owner_login_verified':False,'recovery_verified':False,'production_ready':False}
        data=p.encoded(handoff);destination=INPUTS/'qualification'
        if destination.exists():private_directory(destination)
        elif destination.is_symlink():raise InstallError('installer_collect_redirected_qualification')
        for name,body in reports.items():
            path=destination/(name+'.json')
            if os.path.lexists(path) and secured(path).read_bytes()!=body:
                raise InstallError('installer_collect_existing_finalizer_differs')
        output=INPUTS/('installed-handoff-'+plan['options']['operation_id']+'.json')
        if os.path.lexists(output) and secured(output).read_bytes()!=data:raise InstallError('installer_collect_existing_handoff_differs')
        # All nine real source reports/receipts are checked before any output.
        p.require_capacity(INPUTS,p.file_tree_storage_bound({**{'qualification/'+name+'.json':len(body) for name,body in reports.items()},output.name:len(data)},os.statvfs(INPUTS).f_frsize))
        inputs.recheck()
        if not destination.exists():destination.mkdir(mode=0o700)
        for name,body in reports.items():write_new(destination/(name+'.json'),body)
        write_new(output,data)
        inputs.recheck()
        return {'state':'actual-install-evidence-preserved','handoff':str(output),
            'qualification_directory':str(destination),'firmware':handoff['firmware'],
            'detached_boots_collected':0,'production_ready':False}
    finally:os.close(lock)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--review',required=True,type=Path,help='Actual saved review envelope; contains no credential')
    args=parser.parse_args()
    if os.getuid()!=0 or os.geteuid()!=0:raise InstallError('installer_collect_root_coordinator_required')
    os.umask(0o077)
    print(payload_module().encoded(collect(read_review(args.review),NativeInputs(),LinuxDisk())).decode(),end='')


if __name__=='__main__':main()

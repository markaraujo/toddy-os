#!/usr/bin/env python3
"""Seal actual native image/boot evidence for the fixed live installer factory.

This tool does not install, format, boot, sign, download or invent qualification.
Inputs must already exist from the designated guest's native source callbacks.
"""
import argparse
import hashlib
import os
from pathlib import Path
import shutil
import sys

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from runtime.installer.composition import SOURCES,source_path,secured,validate_boot_evidence,validate_finalizer_report,bundle_namespace,validate_policy
from runtime.installer.native_finalizer import payload_module,account_files
from runtime.installer.installed_boot import InstalledBoot
from runtime.installer.disk_plan import InstallError
from scripts.build.phase2.owner_setting_evidence import validate_companion


def seal(image,inputs,output):
    p=payload_module();image=Path(image);inputs=Path(inputs);output=Path(output)
    if os.geteuid()!=0:raise InstallError('installer_composition_designated_guest_root_required')
    if any(path.resolve()!=path or not path.is_absolute() or path==Path('/') for path in (image,inputs,output)) or \
            not image.is_dir() or not inputs.is_dir() or output.exists() or output.is_symlink() or \
            not output.parent.is_dir() or not output.is_relative_to('/sources/stage') or \
            image.is_relative_to(inputs) or inputs.is_relative_to(image) or output.is_relative_to(inputs) or output.is_relative_to(image):
        raise InstallError('installer_composition_fresh_designated_stage_required')
    def read(relative):return p.strict(secured(inputs/relative).read_bytes())
    manifest_path=secured(inputs/'payload/manifest.json');manifest_sha=p.digest(manifest_path)
    manifest=p.PreparedPayload(inputs/'payload',manifest_sha256=manifest_sha,runner=None,finalizer=None)._load()
    bundle_namespace(inputs/'payload',manifest)
    policy=read('policy.json');validate_policy(policy,manifest)
    generated=read('generated-entries.json');boot=read('boot-profile.json')
    InstalledBoot(inputs/'payload',manifest,boot,None)
    snapshot=p.PreparedPayload.audit_tree(image,manifest,generated)
    image_sha=hashlib.sha256(p.encoded(snapshot)).hexdigest()
    descriptor={'schema_version':1,'payload_manifest_sha256':manifest_sha,'catalog_sha256':manifest['catalog_sha256'],
                'policy_sha256':p.digest(secured(inputs/'policy.json')),
                'generated_entries_sha256':p.digest(secured(inputs/'generated-entries.json')),
                'image_manifest_sha256':image_sha,'boot_profile_sha256':p.digest(secured(inputs/'boot-profile.json')),
                'source_sha256':{name:p.digest(secured(source_path(name))) for name in sorted(SOURCES)}}
    checks={}
    for check in sorted(p.CHECKS):
        report=read('qualification/'+check+'.json');validate_finalizer_report(report,check,descriptor)
        checks[check]=p.digest(secured(inputs/'qualification'/(check+'.json')))
    firmware={};owner_settings={}
    for name in ('bios','uefi'):
        path=inputs/'qualification'/('boot-'+name+'.json')
        if path.exists() or path.is_symlink():
            report=read('qualification/boot-'+name+'.json');validate_boot_evidence(report,name,descriptor,boot)
            firmware[name]=p.digest(secured(path))
            companion=inputs/'qualification'/('owner-settings-'+name+'.json')
            validate_companion(read('qualification/'+companion.name),report,firmware[name])
            owner_settings[name]=p.digest(secured(companion))
    if not firmware:raise InstallError('installer_composition_no_native_detached_boot_receipt')
    qualification={'kind':'native-installer-composition-v1','input_manifest_sha256':manifest_sha,
                   'source_sha256':descriptor['source_sha256'],'image_manifest_sha256':image_sha,
                   'checks':checks,'firmware_reports':firmware}
    descriptor['qualification_sha256']=hashlib.sha256(p.encoded(qualification)).hexdigest()
    # Validate every copied file's root custody, including the signed archives,
    # before creating the output. The payload is archive inputs, never root copy.
    for base,directories,files in os.walk(inputs/'payload',followlinks=False):
        for name in directories:
            path=Path(base)/name
            if path.is_symlink() or path.resolve()!=path:raise InstallError('installer_composition_redirected_payload')
        for name in files:secured(Path(base)/name,limit=8*1024**3)
    output.mkdir(mode=0o700)
    # A failed copy is retained as incomplete; composition.json is published last.
    shutil.copytree(inputs/'payload',output/'payload')
    (output/'qualification').mkdir(mode=0o700)
    for name in ('policy.json','generated-entries.json','boot-profile.json'):
        shutil.copyfile(inputs/name,output/name);(output/name).chmod(0o400)
    for name in [*checks,*('boot-'+name for name in firmware)]:
        shutil.copyfile(inputs/'qualification'/(name+'.json'),output/'qualification'/(name+'.json'))
        (output/'qualification'/(name+'.json')).chmod(0o400)
    (output/'qualification.json').write_bytes(p.encoded(qualification));(output/'qualification.json').chmod(0o400)
    # Recheck all copied custody and native archive signature bindings; no inputs
    # may change between independent image audit and publishing the descriptor.
    copied=p.PreparedPayload(output/'payload',manifest_sha256=manifest_sha,runner=None,finalizer=None)._load()
    if copied!=manifest or p.PreparedPayload.audit_tree(image,manifest,generated)!=snapshot:raise InstallError('installer_composition_inputs_changed')
    for name in ('policy.json','generated-entries.json','boot-profile.json'):
        if p.digest(output/name)!=p.digest(secured(inputs/name)):raise InstallError('installer_composition_copy_changed')
    for name,digest in {**checks,**{'boot-'+name:digest for name,digest in firmware.items()}}.items():
        if p.digest(output/'qualification'/(name+'.json'))!=digest:raise InstallError('installer_composition_report_copy_changed')
    for name,digest in descriptor['source_sha256'].items():
        if p.digest(secured(source_path(name)))!=digest:raise InstallError('installer_composition_source_changed')
    (output/'composition.json').write_bytes(p.encoded(descriptor));(output/'composition.json').chmod(0o400)
    fd=os.open(output,os.O_RDONLY|os.O_DIRECTORY)
    try:os.fsync(fd)
    finally:os.close(fd)
    return {'state':'sealed-native-composition-inputs','composition_sha256':p.digest(output/'composition.json'),
            'payload_manifest_sha256':manifest_sha,'image_manifest_sha256':image_sha,'supported_firmware':sorted(firmware),'owner_settings_sha256':owner_settings,
            'installed_factory_path':'/usr/share/toddy/installer/composition','disk_writes':False}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--image',required=True,type=Path);parser.add_argument('--inputs',required=True,type=Path);parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args()
    print(payload_module().encoded(seal(args.image,args.inputs,args.output)).decode(),end='')

if __name__=='__main__':main()

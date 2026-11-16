#!/usr/bin/env python3
"""Root coordinator's first blank-VM source harness; never a live factory option.

This development tool is not packaged or exposed by Polkit. Production Calamares
always uses live_bindings.create(), including its retained detached-boot gate.
"""
import argparse
import hashlib
import os
from pathlib import Path
import signal
import resource
import sys

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from runtime.installer.backend import Installer,Journal
from runtime.installer.calamares.adapter import sealed_json,PipeCancellation
from runtime.installer.composition import secured,bundle_namespace,validate_policy,validate_owner_options,validate_installed_handoff,source_path,SOURCES
from runtime.installer.disk_plan import InstallError,QualificationPolicy,make_plan,validate_plan
from runtime.installer.installed_boot import InstalledBoot
from runtime.installer.linux_disk import LinuxDisk
from runtime.installer.native_finalizer import NativeFinalizer,payload_module

INPUTS=Path('/sources/stage/toddy-installer-native-inputs')
JOURNAL=Path('/var/lib/toddy/installer-qualification')


class NativeInputs:
    """Pinned actual native image inputs, deliberately no readiness() API.

    Signed packages, reviewed image projection and fixed callback code are still
    required. Only retained BIOS/UEFI boot evidence is collected by this harness,
    rather than asserted before the first boot. No marker becomes production-ready.
    """
    directory=INPUTS

    def __init__(self):
        self.bundle=self.directory/'payload';self.recheck()

    def recheck(self):
        p=payload_module()
        paths=('payload/manifest.json','policy.json','generated-entries.json','boot-profile.json','expected-image-manifest.json')
        pins={name:p.digest(secured(self.directory/name)) for name in paths}
        source_hashes={name:p.digest(secured(source_path(name))) for name in SOURCES}
        pins.update({'source:'+name:digest for name,digest in source_hashes.items()})
        if hasattr(self,'pins') and self.pins!=pins:raise InstallError('installer_qualification_inputs_changed')
        self.pins=pins
        read=lambda name:p.strict(secured(self.directory/name).read_bytes())
        self.manifest=p.PreparedPayload(self.bundle,manifest_sha256=pins['payload/manifest.json'],runner=None,finalizer=None)._load()
        bundle_namespace(self.bundle,self.manifest);validate_installed_handoff(self.manifest,source_hashes)
        self.policy=read('policy.json');validate_policy(self.policy,self.manifest)
        self.generated=read('generated-entries.json');self.boot=read('boot-profile.json')
        expected=read('expected-image-manifest.json')
        self.descriptor={'payload_manifest_sha256':pins['payload/manifest.json'],'policy_sha256':pins['policy.json'],
                         'image_manifest_sha256':hashlib.sha256(p.encoded(expected)).hexdigest()}
        InstalledBoot(self.bundle,self.manifest,self.boot,None)


def callbacks(inputs,system):
    p=payload_module()
    native=p.PreparedPayload(inputs.bundle,manifest_sha256=inputs.descriptor['payload_manifest_sha256'],runner=system,finalizer=NativeFinalizer(inputs,system))
    def verify(plan):
        inputs.recheck();validate_owner_options(inputs.policy,plan['options'])
        return native.verify_payload(plan)
    def install(root,plan):
        verify(plan);return native.install_payload(root,plan)
    def pending(root,plan):
        inputs.recheck();options=plan['options']
        request={key:options[key] for key in ('operation_id','uid','gid','username','ai_choice','extras')}
        request['catalog_sha256']=plan['payload']['catalog_sha256']
        command=['/usr/bin/chroot','--userspec='+str(options['uid'])+':'+str(options['gid']),'--groups='+str(options['gid']),str(root),
                 '/usr/bin/env','-i','PATH=/usr/bin:/usr/sbin','HOME=/home/'+options['username'],'LANG=C.UTF-8',
                 '/usr/bin/python3','-I','/usr/lib/toddy/setup/installer_handoff.py']
        return p.strict(system.run(command,data=p.encoded(request)).encode())
    return verify,install,InstalledBoot(inputs.bundle,inputs.manifest,inputs.boot,system),pending


def main(*,inputs_type=NativeInputs):
    if os.getuid()!=0 or os.geteuid()!=0:raise SystemExit('installer_qualification_root_coordinator_required')
    resource.setrlimit(resource.RLIMIT_CORE,(0,0));os.umask(0o077)
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='action',required=True)
    review=sub.add_parser('review');review.add_argument('--options-fd',required=True,type=int);review.add_argument('--serial',required=True)
    execute=sub.add_parser('execute');execute.add_argument('--plan-fd',required=True,type=int)
    execute.add_argument('--credential-fd',required=True,type=int);execute.add_argument('--cancel-fd',required=True,type=int)
    execute.add_argument('--confirm',required=True);execute.add_argument('--serial',required=True)
    gui=sub.add_parser('gui');gui.add_argument('--uid',required=True,type=int);gui.add_argument('--display',required=True)
    gui.add_argument('--locale',choices=('en_US.UTF-8','pt_BR.UTF-8'),default='en_US.UTF-8')
    args=parser.parse_args()
    if args.action=='gui':
        from runtime.installer.launch import qualification_command
        command,environment=qualification_command(args.uid,args.display,args.locale)
        os.execve(command[0],command,environment)
    inputs=inputs_type();system=LinuxDisk();policy=QualificationPolicy(args.serial)
    if args.action=='review':
        request=sealed_json(args.options_fd)
        if not isinstance(request,dict) or set(request)!={'device','options'}:raise InstallError('installer_qualification_options')
        validate_owner_options(inputs.policy,request['options'])
        disk=system.probe(request['device']);policy.check(disk)
        p=payload_module();manifest=inputs.manifest
        plan=make_plan(disk,request['options'],{'sha256':inputs.descriptor['payload_manifest_sha256'],'catalog_sha256':manifest['catalog_sha256'],'bytes':manifest['bytes']})
        print(p.encoded({'state':'qualification-review-only','disk_writes':False,'plan':plan}).decode(),end='')
        return
    if len({args.plan_fd,args.credential_fd,args.cancel_fd})!=3:raise InstallError('installer_qualification_private_descriptors')
    plan=validate_plan(sealed_json(args.plan_fd));policy.check(plan['target']);validate_owner_options(inputs.policy,plan['options'])
    if args.confirm!=plan['plan_sha256']:raise InstallError('installer_confirmation_mismatch')
    verify,install,boot,pending=callbacks(inputs,system);verify(plan)
    cancel=PipeCancellation(args.cancel_fd)
    for number in (signal.SIGTERM,signal.SIGINT,signal.SIGHUP):signal.signal(number,lambda *_:cancel.request())
    journal=Journal(JOURNAL)
    try:
        backend=Installer(journal,policy=policy,verify_payload=verify,install_payload=install,build_boot=boot,save_pending=pending,system=system)
        # Explicit exact root-coordinator review, with the existing independent
        # final disk re-probe, VM serial policy and safe cancellation checks.
        def authorize(current):
            policy.check(current['target'])
            return args.confirm==current['plan_sha256']==plan['plan_sha256']
        result=backend.execute(plan,confirmation=args.confirm,authorize=authorize,credential_fd=args.credential_fd,cancel=cancel)
        print(payload_module().encoded({'scope':'trusted-blank-VM-source-qualification-not-production-readiness',**result}).decode(),end='')
    finally:journal.close()

if __name__=='__main__':
    try:main()
    except (ValueError,OSError,KeyError,TypeError):raise SystemExit('installer_qualification_failed_no_automatic_retry') from None

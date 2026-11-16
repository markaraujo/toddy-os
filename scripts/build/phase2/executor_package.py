"""Deterministic original-source executor payload; no runtime grant or host install."""
import hashlib
import json
import os
from pathlib import Path
import shutil

VERSION='0.2.0-1+toddy1'
DEPENDENCIES=('python (>= 3.14.10-1+toddy2), python (<< 3.15), '
              'pygobject (= 3.56.3-1+toddy1), glib (>= 2.88.3-1+toddy2), '
              'dbus (>= 1.16.2-1+toddy1), polkit (= 127-1+toddy1), '
              'systemd (>= 261.2-1+toddy3), apt, dpkg, networkmanager (= 1.58.1-1+toddy1)')
MODULES=('service.py','store.py','policy.py','owner_policy.py','operations.py','configuration.py',
         'native_backends.py','command_child.py','linux_identity.py','session_identity.py',
         'io.github.markaraujo.Toddy.Executor1.xml')


def stage(destination,repository):
    destination=Path(destination);repository=Path(repository)
    if not destination.is_absolute() or destination.resolve()!=destination or destination.exists() or destination.is_symlink():
        raise ValueError('executor_stage_must_be_new_canonical_directory')
    inputs={};outputs={}
    def copy(relative,target,mode=0o644):
        source=repository/relative
        if source.is_symlink() or not source.is_file() or not source.resolve().is_relative_to(repository.resolve()):
            raise ValueError('executor_source_not_regular')
        output=destination/target.lstrip('/');output.parent.mkdir(mode=0o755,parents=True,exist_ok=True)
        data=source.read_bytes();output.write_bytes(data);output.chmod(mode)
        digest=hashlib.sha256(data).hexdigest();inputs[relative]=digest;outputs[target]={'sha256':digest,'mode':format(mode,'04o')}
    for name in MODULES:
        copy('runtime/executor/'+name,'/usr/lib/toddy/executor/'+name,0o755 if name=='owner_policy.py' else 0o644)
    for name,target in [('toddy-executor.service','/usr/lib/systemd/system/toddy-executor.service'),
             ('io.github.markaraujo.Toddy.Executor.conf','/usr/share/dbus-1/system.d/io.github.markaraujo.Toddy.Executor.conf'),
             ('io.github.markaraujo.Toddy.Owner.policy','/usr/share/polkit-1/actions/io.github.markaraujo.Toddy.Owner.policy')]:
        copy('runtime/executor/packaging/'+name,target)
    doc=destination/'usr/share/doc/toddy-executor';doc.mkdir(parents=True,exist_ok=True)
    copy('LICENSE','/usr/share/doc/toddy-executor/copyright')
    copy('LICENSES/CC-BY-4.0.txt','/usr/share/doc/toddy-executor/CC-BY-4.0.txt')
    activation=destination/'usr/share/dbus-1/system-services/io.github.markaraujo.Toddy.Executor.service'
    activation.parent.mkdir(parents=True,exist_ok=True)
    activation.write_text('[D-BUS Service]\nName=io.github.markaraujo.Toddy.Executor\nExec=/usr/bin/false\nUser=root\nSystemdService=toddy-executor.service\n')
    # Without systemd activation the root executor deliberately stays unavailable;
    # a direct D-Bus launch must not bypass its qualified cgroup lifetime.
    enabled=destination/'etc/systemd/system/multi-user.target.wants/toddy-executor.service'
    enabled.parent.mkdir(parents=True,exist_ok=True);enabled.symlink_to('/usr/lib/systemd/system/toddy-executor.service')
    (doc/'README').write_text('''Toddy privileged executor

Original Python sources are MIT; documentation is CC BY4.0. No model, GTK,
plugin, credential or root grant is bundled. The package depends only on the
already selected native distribution stack, never an Ubuntu repository.

The root service creates private /var/lib/toddy/executor state using its systemd
StateDirectory. No database or administrative grant belongs in a live image.
After reviewed native acquisition, reload the system manager and start this unit
at a safe transaction boundary. D-Bus activation requires systemd; the fallback
Exec is false so it cannot start an uncontained root process.

The owner surface is the exact root-owned executable:
  pkexec /usr/lib/toddy/executor/owner_policy.py grant --mode session --expires-in 3600
Use --mode standing only deliberately. Each action requires administrator
authentication; full administration can change the entire system. A session grant
is bounded by the exact active/unlocked/local owner logind session. Revoke with:
  pkexec /usr/lib/toddy/executor/owner_policy.py revoke

Root rescue can invoke policy.py directly with --uid and a deliberate action.
Stop/revoke block future dispatch; committed writes are not automatically undone.
Before removal/upgrade, stop new dispatch and reconcile pending package/boot
operations at their safe boundary. Stop the unit before removing its code; do not
delete the private database as an automatic cleanup or replay uncertain work.
The existing package transaction/acquisition controller must perform manager
reload/restart postconditions; this payload imports no maintainer scripts.
''')
    inputs['scripts/build/phase2/executor_package.py']=hashlib.sha256((repository/'scripts/build/phase2/executor_package.py').read_bytes()).hexdigest()
    manifest={'schema_version':1,'package':'toddy-executor','version':VERSION,
              'source_license':'MIT','inputs':inputs,'source_outputs':outputs,
              'runtime_state':'/var/lib/toddy/executor','bundled_grants':False,
              'activation':'systemd-only; explicit reviewed acquisition activation required'}
    (doc/'source-manifest.json').write_text(json.dumps(manifest,sort_keys=True,indent=2)+'\n')
    for path in destination.rglob('*'):
        if not path.is_symlink() and path.is_dir():path.chmod(0o755)
        elif not path.is_symlink() and path not in [destination/'usr/lib/toddy/executor/owner_policy.py']:path.chmod(0o644)
    for path in [*destination.rglob('*'),destination]:
        os.utime(path,(1794009600,1794009600),follow_symlinks=False)
    return manifest

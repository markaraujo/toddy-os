"""Managed ordinary argv execution under a user-systemd scope tied to the broker.

Scope creation/verification precedes the trusted launcher gate. A missing manager
or parent unit disables this route; no uncontained production shell fallback.
"""
import json
import os
from pathlib import Path
import re
import selectors
import signal
import subprocess
import sys
import tempfile
import time
import uuid
from .native import ToolError, validate_shell


class ScopedShell:
    def __init__(self, parent_unit='toddy-agent.service'):
        if not re.fullmatch(r'toddy-[a-z0-9-]{1,96}\.service', parent_unit):
            raise ToolError('invalid_managed_parent')
        self.parent_unit=parent_unit

    def _command(self, args, environment, *, check=True):
        r=subprocess.run(['/usr/bin/systemctl','--user',*args],stdin=subprocess.DEVNULL,
                         capture_output=True,text=True,env=environment,timeout=10)
        if check and r.returncode:raise ToolError('managed_shell_unavailable')
        return r

    def _properties(self, unit, environment):
        r=self._command(['show',unit,'-p','LoadState','-p','ActiveState','-p','ControlGroup',
                         '-p','MainPID','-p','KillMode','--no-pager'],environment,check=False)
        return dict(line.split('=',1) for line in r.stdout.splitlines() if '=' in line)

    def __call__(self, workspace, argv, *, timeout_seconds=30, canceled=lambda:False):
        validate_shell(argv,timeout_seconds)
        if os.getuid()==0 or os.geteuid()==0:raise ToolError('unprivileged_tools_required')
        if canceled():raise ToolError('canceled_before_dispatch')
        uid=os.getuid();workspace=Path(workspace)
        if not workspace.is_absolute() or workspace.resolve()!=workspace or workspace.stat().st_uid!=uid or workspace.stat().st_mode&0o022:
            raise ToolError('unsafe_workspace')
        env={'PATH':'/usr/bin:/usr/sbin','LANG':'C.UTF-8','HOME':str(workspace),
             'XDG_RUNTIME_DIR':'/run/user/'+str(uid),
             'DBUS_SESSION_BUS_ADDRESS':'unix:path=/run/user/'+str(uid)+'/bus'}
        parent=self._properties(self.parent_unit,env)
        own=Path('/proc/self/cgroup').read_text().splitlines()
        if (parent.get('ActiveState')!='active' or parent.get('MainPID')!=str(os.getpid())
                or parent.get('KillMode')!='control-group' or not parent.get('ControlGroup')
                or '0::'+parent['ControlGroup'] not in own):
            raise ToolError('managed_shell_parent_unavailable')
        unit='toddy-task-'+uuid.uuid4().hex+'.scope'
        deadline=time.monotonic()+timeout_seconds;group=None;process=None;chunks=[];size=0
        with tempfile.TemporaryDirectory(prefix='.toddy-scope-',dir=workspace) as name:
            folder=Path(name);folder.chmod(0o700)
            command=['/usr/bin/systemd-run','--user','--scope','--quiet','--collect','--unit='+unit,
                     '--property=BindsTo='+self.parent_unit,'--property=After='+self.parent_unit,
                     '--property=KillMode=control-group','--property=TimeoutStopSec=3s',
                     '--property=RuntimeMaxSec='+str(timeout_seconds+15)+'s',
                     '/usr/bin/python3','-I',str(Path(__file__).with_name('scoped_child.py')),
                     str(os.getpid()),Path('/proc/self/stat').read_text().split()[21],str(folder),*argv]
            try:
                process=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,cwd=workspace,env=env,start_new_session=True,close_fds=True,umask=0o077)
                ready=folder/'ready'
                while not ready.exists():
                    if canceled():raise ToolError('canceled_effects_unverified')
                    if process.poll() is not None:raise ToolError('managed_scope_start_failed')
                    if time.monotonic()>=deadline:raise ToolError('shell_deadline')
                    time.sleep(.01)
                row=json.loads(ready.read_text());pid=row['pid']
                if type(pid) is not int or pid<=0 or row['uid']!=uid:raise ToolError('managed_scope_unverified')
                props=self._properties(unit,env);group=props.get('ControlGroup')
                if not group or group.startswith('/../') or '0::'+group not in Path('/proc',str(pid),'cgroup').read_text().splitlines():
                    raise ToolError('managed_scope_unverified')
                if canceled():raise ToolError('canceled_before_dispatch')
                (folder/'go').touch(mode=0o600,exist_ok=False)
                with selectors.DefaultSelector() as selector:
                    selector.register(process.stdout,selectors.EVENT_READ)
                    while selector.get_map():
                        if canceled():raise ToolError('canceled_effects_unverified')
                        if time.monotonic()>=deadline:raise ToolError('shell_deadline')
                        for key,_ in selector.select(.05):
                            data=os.read(key.fd,8192)
                            if not data:selector.unregister(key.fileobj);continue
                            size+=len(data)
                            if size>65536:raise ToolError('shell_output_limit')
                            chunks.append(data)
                while process.poll() is None:
                    if canceled():raise ToolError('canceled_effects_unverified')
                    if time.monotonic()>=deadline:raise ToolError('shell_deadline')
                    time.sleep(.01)
                result={'process_exit_verified':True,'exit':process.returncode,
                        'output':b''.join(chunks).decode('utf-8',errors='replace'),
                        'side_effects_verified':False,'uid':uid,'managed_scope':True}
            finally:
                # Stop the entire scope including descendants that used setsid.
                # Kill the trusted runner too, then stop again for registration races.
                cleanup_error=False
                try:self._command(['stop',unit],env,check=False)
                except (OSError,subprocess.SubprocessError):cleanup_error=True
                if process is not None:
                    # A known exited runner has already been reaped by poll;
                    # never signal a group using its potentially reusable PID.
                    if process.returncode is None:
                        try:os.killpg(process.pid,signal.SIGKILL)
                        except ProcessLookupError:pass
                    process.wait(timeout=5);process.stdout.close()
                try:
                    self._command(['stop',unit],env,check=False)
                    state=self._properties(unit,env)
                except (OSError,subprocess.SubprocessError):
                    cleanup_error=True;state={}
                path=Path('/sys/fs/cgroup')/group.lstrip('/')/'cgroup.procs' if group else None
                if (cleanup_error or state.get('ActiveState') not in (None,'inactive','failed')
                        or (path and path.exists() and path.read_text().strip())):
                    raise ToolError('managed_scope_cleanup_unverified')
            return {**result,'managed_processes_stopped':True}

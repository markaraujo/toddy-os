"""Default-policy active PAM session grants and native executor package lifecycle."""
import base64
import hashlib
import json
import os
from pathlib import Path
import pty
import re
import secrets
import select
import signal
import subprocess
import time
import zlib


def run(argv, timeout=30, check=True):
    r=subprocess.run(argv,capture_output=True,text=True,timeout=timeout,
                     env={'PATH':'/usr/bin:/usr/sbin','LANG':'C.UTF-8','HOME':'/root'})
    assert not check or r.returncode==0, ('command_failed',argv[:3],r.returncode,r.stderr[:300])
    return r


def emit(report):
    raw=json.dumps(report,sort_keys=True).encode();packed=base64.b64encode(zlib.compress(raw,9)).decode()
    chunks=[packed[i:i+1024] for i in range(0,len(packed),1024)]
    for i,c in enumerate(chunks):print('TODDY_B02_RUNTIME_DATA',i,c,flush=True)
    print('TODDY_B02_RUNTIME_RESULT',json.dumps({'kernel':os.uname().release,
          'all_selected_exits_zero':report['all_selected_exits_zero'],'report_sha256':hashlib.sha256(raw).hexdigest(),'chunks':len(chunks)}),flush=True)


def main():
    assert os.geteuid()==0 and os.uname().release=='7.1.8-toddy' and Path('/proc/1/comm').read_text().strip()=='systemd'
    assert run(['systemd-detect-virt','--vm']).stdout.strip() in ('kvm','qemu')
    device=run(['findmnt','-n','-o','SOURCE','/']).stdout.strip();assert re.fullmatch('/dev/[a-z0-9]+',device)
    parent=run(['lsblk','-ndo','PKNAME',device]).stdout.strip();assert re.fullmatch('[a-z0-9]+',parent)
    assert run(['lsblk','-dnro','SERIAL','/dev/'+parent]).stdout.strip()=='TODDY-BOOT-TEST'
    credentials=Path(os.environ['CREDENTIALS_DIRECTORY']);manifest=json.loads((credentials/'toddy.executor.manifest').read_text())
    packed=b''.join((credentials/('toddy.executor.input'+str(i))).read_bytes() for i in range(manifest['chunks']))
    assert hashlib.sha256(packed).hexdigest()==manifest['sha256'];files=json.loads(zlib.decompress(packed))
    assert not Path('/usr/lib/toddy/executor').exists()
    stage=Path('/tmp/toddy-executor-package');stage.mkdir(mode=0o755)
    root=stage/'usr/lib/toddy/executor';root.mkdir(parents=True)
    hashes={}
    for name,text in files.items():
        assert name==Path(name).name and name.endswith(('.py','.xml'))
        target=root/name;target.write_text(text);target.chmod(0o755 if name=='owner_policy.py' else 0o644)
        hashes[name]=hashlib.sha256(target.read_bytes()).hexdigest()
    for name,destination in manifest['packaging'].items():
        path=Path(destination['path']);assert str(path).startswith(('/etc/dbus-1/','/etc/systemd/','/usr/share/polkit-1/')) and not path.exists()
        target=stage/str(path).lstrip('/');target.parent.mkdir(parents=True,exist_ok=True);target.write_text(destination['text']);target.chmod(0o644)
        hashes[name]=hashlib.sha256(target.read_bytes()).hexdigest()
    control=stage/'DEBIAN';control.mkdir(mode=0o755)
    # Fixture package versions prove native lifecycle, not a signed release catalog.
    def install(version):
        (control/'control').write_text('Package: toddy-executor\nVersion: 0.1-'+str(version)+'+toddy1\nArchitecture: amd64\nMaintainer: Toddy OS\nDescription: Disposable native executor lifecycle qualification\n')
        (control/'postinst').write_text('#!/bin/sh\nset -eu\nsystemctl daemon-reload\nsystemctl try-restart toddy-executor.service\n')
        (control/'postinst').chmod(0o755)
        archive=Path('/tmp/toddy-executor-'+str(version)+'.deb')
        run(['dpkg-deb','--root-owner-group','--build',str(stage),str(archive)])
        run(['dpkg','--install',str(archive)])
        assert run(['dpkg-query','-W','-f=${Version}','toddy-executor']).stdout=='0.1-'+str(version)+'+toddy1'
        assert not run(['dpkg','--audit']).stdout.strip()
        for name,digest in hashes.items():
            path=(Path('/usr/lib/toddy/executor')/name if name in files else Path(manifest['packaging'][name]['path']))
            assert hashlib.sha256(path.read_bytes()).hexdigest()==digest
            assert path.stat().st_uid==0 and not path.stat().st_mode&0o022
            assert run(['dpkg-query','-S',str(path)]).stdout.startswith('toddy-executor: ')
    install(1)
    run(['dbus-send','--system','--type=method_call','--print-reply','--dest=org.freedesktop.DBus','/','org.freedesktop.DBus.ReloadConfig'])
    Path('/var/lib/toddy').mkdir(mode=0o755,exist_ok=True)
    run(['systemctl','start','polkit.service','systemd-logind.service','toddy-executor.service'])
    username='toddy-policy-owner';uid=12405
    run(['useradd','-m','-U','-u',str(uid),'-G','wheel','-s','/bin/bash',username])
    secret=secrets.token_urlsafe(32)
    r=subprocess.run(['chpasswd','-c','YESCRYPT'],input=username+':'+secret+'\n',text=True,capture_output=True,timeout=15)
    assert r.returncode==0,'Ephemeral credential creation failed'
    report={'scope':'Trusted root-created native PAM/logind local session, default Polkit owner policy with real administrator password, session grants and dpkg install/upgrade/revoke. No authorization-rule override or real console/GDM login claim; graphical UI/physical/signed release acceptance separate.',
            'source_sha256':hashes,'all_selected_exits_zero':False,'checks':[]}
    def passed(name,**data):report['checks'].append({'name':name,**data});print('TODDY_B04_STAGE',name,flush=True)
    policy=Path('/run/toddy-executor-owner-pam');policy.mkdir(mode=0o755)
    (policy/'toddy-session').write_text('account required pam_unix.so\nsession required pam_systemd.so\n')
    pid,fd=pty.fork()
    if pid==0:
        # Trusted root fixture opens a real PAM/logind session; owner grant still
        # requires independent pkexec/PAM password authentication below.
        import ctypes
        lib=ctypes.CDLL('libpam.so.0')
        class Conversation(ctypes.Structure):pass
        Callback=ctypes.CFUNCTYPE(ctypes.c_int,ctypes.c_int,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p)
        cb=Callback(lambda *_:19)
        Conversation._fields_=[('conv',Callback),('data',ctypes.c_void_p)]
        conv=Conversation(cb,None);handle=ctypes.c_void_p()
        lib.pam_start_confdir.argtypes=[ctypes.c_char_p,ctypes.c_char_p,ctypes.POINTER(Conversation),ctypes.c_char_p,ctypes.POINTER(ctypes.c_void_p)]
        assert lib.pam_start_confdir(b'toddy-session',username.encode(),ctypes.byref(conv),str(policy).encode(),ctypes.byref(handle))==0
        lib.pam_set_item.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_void_p]
        lib.pam_putenv.argtypes=[ctypes.c_void_p,ctypes.c_char_p]
        assert lib.pam_set_item(handle,3,ctypes.c_char_p(b'tty1'))==0
        assert lib.pam_putenv(handle,b'XDG_SESSION_TYPE=tty')==0
        assert lib.pam_putenv(handle,b'XDG_SESSION_CLASS=user')==0
        assert lib.pam_acct_mgmt(handle,0)==0
        assert lib.pam_open_session(handle,0)==0
        shellpid=os.fork()
        if shellpid==0:
            os.setgroups([__import__('grp').getgrnam('wheel').gr_gid]);os.setgid(uid);os.setuid(uid)
            os.environ.clear();os.environ.update(PATH='/usr/bin:/usr/sbin',LANG='C.UTF-8',TERM='dumb',HOME='/home/'+username,USER=username,LOGNAME=username,PS1='TODDY_OWNER_SHELL_READY> ')
            os.chdir('/home/'+username)
            os.execv('/usr/bin/bash',['bash','--noprofile','--norc'])
        _,raw=os.waitpid(shellpid,0)
        assert lib.pam_close_session(handle,0)==0
        assert lib.pam_end(handle,0)==0
        os._exit(os.waitstatus_to_exitcode(raw))
    tail=b'';prompts=0;session=None;deadline=time.monotonic()+30
    try:
        while time.monotonic()<deadline:
            if select.select([fd],[],[],.2)[0]:
                try:data=os.read(fd,8192)
                except OSError:data=b''
                tail=(tail+data)[-8192:]
                if re.search(rb'[Pp]assword: *$',tail):
                    prompts+=1;assert prompts==1,'Repeated login authentication prompt'
                    os.write(fd,secret.encode()+b'\n');tail=b''
            r=run(['loginctl','show-user',str(uid),'-p','Display','--value'],check=False)
            if r.returncode==0 and re.fullmatch(r'[a-zA-Z0-9_-]{1,128}',r.stdout.strip()):session=r.stdout.strip();break
        assert prompts==0 and session is not None,'Root-created local PAM/logind session missing'
        # logind can be ready before Bash finishes tty setup; wait for its real
        # prompt so readline cannot flush a command submitted during startup.
        until=time.monotonic()+10
        while b'TODDY_OWNER_SHELL_READY> ' not in tail and time.monotonic()<until:
            if select.select([fd],[],[],.1)[0]:
                try:tail=(tail+os.read(fd,8192))[-8192:]
                except OSError:break
        assert b'TODDY_OWNER_SHELL_READY> ' in tail,'Owner interactive shell readiness missing'

        props=dict(l.split('=',1) for l in run(['loginctl','show-session',session,'-p','User','-p','Active','-p','Remote','-p','Type']).stdout.splitlines())
        assert props['User']==str(uid) and props['Active']=='yes' and props['Remote']=='no'
        passed('trusted-root-pam-active-local-logind-session',properties=props,raw_tty_retained=False)
        def shell(command, *, authenticate=False, success=True):
            os.write(fd,(command+"; printf '\\nTODDY_COMMAND_DONE:%s\\n' $?\n").encode())
            tail=b'';count=0;deadline=time.monotonic()+40
            while time.monotonic()<deadline:
                if select.select([fd],[],[],.2)[0]:
                    try:data=os.read(fd,8192)
                    except OSError:data=b''
                    tail=(tail+data)[-32768:]
                    if re.search(rb'[Pp]assword: *$',tail):
                        count+=1;assert authenticate and count<=1,'Unexpected PAM prompt'
                        os.write(fd,secret.encode()+b'\n');tail=b''
                    match=re.search(rb'(?:\r?\n)TODDY_COMMAND_DONE:([0-9]+)\r?\n',tail)
                    if match:
                        code=int(match[1]);assert (code==0)==success,('shell_status',code)
                        assert not authenticate or count==1,'Expected fresh administrator authentication'
                        return tail
            raise AssertionError(('Owner shell command deadline',{'password_prompts':count,'known_markers':{word:word.encode() in tail for word in ['Authentication failure','not authorized','No authentication agent found','TODDY_COMMAND_DONE','TODDY_OWNER_SHELL_READY','Password:']}}))
        helper='/usr/bin/pkexec /usr/lib/toddy/executor/owner_policy.py'
        shell(helper+' grant --mode session --expires-in 300',authenticate=True)
        # Root inspects authority, never writes grants on this path.
        import sys
        sys.path.insert(0,'/usr/lib/toddy/executor');from store import Store
        store=Store(Path('/var/lib/toddy/executor'))
        a={'path':'/etc/toddy-session-proof.conf','text':'session-authorized\n','expected_sha256':None}
        # Execute on the actual login shell through the canonical system-bus API.
        client=Path('/tmp/toddy-owner-ipc.py')
        client.write_text('''import gi,json,sys
from gi.repository import Gio,GLib
c=Gio.bus_get_sync(Gio.BusType.SYSTEM,None)
a={"path":"/etc/toddy-session-proof.conf","text":"session-authorized\\n","expected_sha256":None}
v=GLib.Variant('(sss)',('session-write','config_replace',json.dumps(a)))
for method in ['PlanOperation','DispatchOperation']:
 r=c.call_sync('io.github.markaraujo.Toddy.Executor','/io/github/markaraujo/Toddy/Executor','io.github.markaraujo.Toddy.Executor1',method,v,GLib.VariantType('(s)'),Gio.DBusCallFlags.NONE,10000,None)
 state=json.loads(r.unpack()[0])['state']
 assert state in ('planned','completed') if method=='PlanOperation' else state=='completed'
''');client.chmod(0o644)
        shell('/usr/bin/python3 /tmp/toddy-owner-ipc.py')
        assert Path(a['path']).read_text()==a['text'] and store.inspect(uid,'session-write')['state']=='completed'
        passed('default-active-policy-real-pam-session-grant-and-ipc-effect')
        if 'broker' in manifest:
            exec(compile((credentials/'toddy.broker.hook').read_bytes(),'native-broker-hook','exec'),{**globals(),**locals()})
        outside=Path('/tmp/toddy-user-service-ipc.py')
        outside.write_text(client.read_text().replace('session-write','background-session-write').replace('/etc/toddy-session-proof.conf','/etc/toddy-background-session-proof.conf'));outside.chmod(0o644)
        background=subprocess.run(['/usr/bin/python3',str(outside)],user=uid,group=uid,extra_groups=[],capture_output=True,text=True,timeout=20)
        assert background.returncode==0,('background-owner-session-dispatch',background.returncode,background.stderr[:300])
        assert Path('/etc/toddy-background-session-proof.conf').read_text()==a['text']
        passed('background-same-uid-service-binds-active-owner-logind-display')
        import shlex
        obj=shlex.split(run(['busctl','--system','call','org.freedesktop.login1','/org/freedesktop/login1','org.freedesktop.login1.Manager','GetSession','s',session]).stdout)
        assert len(obj)==2 and obj[0]=='o' and obj[1].startswith('/org/freedesktop/login1/session/')
        run(['busctl','--system','call','org.freedesktop.login1',obj[1],'org.freedesktop.login1.Session','SetLockedHint','b','true'])
        assert run(['loginctl','show-session',session,'-p','LockedHint','--value']).stdout.strip()=='yes'
        locked=Path('/tmp/toddy-locked-session-ipc.py')
        locked.write_text(client.read_text().replace('session-write','locked-session-write').replace('/etc/toddy-session-proof.conf','/etc/toddy-locked-session-proof.conf'));locked.chmod(0o644)
        denied=subprocess.run(['/usr/bin/python3',str(locked)],user=uid,group=uid,extra_groups=[],capture_output=True,text=True,timeout=20)
        assert denied.returncode!=0 and not Path('/etc/toddy-locked-session-proof.conf').exists(),'Locked owner session authorized new background dispatch'
        run(['busctl','--system','call','org.freedesktop.login1',obj[1],'org.freedesktop.login1.Session','SetLockedHint','b','false'])
        assert run(['loginctl','show-session',session,'-p','LockedHint','--value']).stdout.strip()=='no'
        passed('native-logind-locked-hint-refuses-new-background-ipc-and-unlocks')


        install(2)
        assert store.inspect(uid,'session-write')['state']=='completed'
        shell('/usr/bin/python3 /tmp/toddy-owner-ipc.py')
        assert Path(a['path']).read_text()==a['text']
        passed('native-package-owned-upgrade-restart-retains-grant-operation-and-no-replay')
        shell(helper+' revoke',authenticate=True)
        try:store.plan(uid,session,'after-revoke','config_replace',a)
        except Exception as e:assert str(e)=='grant_required',('unexpected_revoke_error',str(e))
        else:raise AssertionError('Revoke did not deny new plan')
        passed('default-active-policy-fresh-authenticated-revoke')
        shell(helper+' grant --mode session --expires-in 300',authenticate=True)
        os.write(fd,b'exit\n')
        waited,raw=os.waitpid(pid,0);assert waited==pid
        # A different/no session cannot use the session-only grant.
        try:store.plan(uid,None,'after-logout','config_replace',a)
        except Exception as e:assert str(e)=='grant_required',('unexpected_logout_error',str(e))
        else:raise AssertionError('Logged-out session grant authorized a caller without session')
        after=Path('/tmp/toddy-after-logout-ipc.py')
        after.write_text(client.read_text().replace('session-write','after-logout-write').replace('/etc/toddy-session-proof.conf','/etc/toddy-after-logout-proof.conf'));after.chmod(0o644)
        denied=subprocess.run(['/usr/bin/python3',str(after)],user=uid,group=uid,extra_groups=[],capture_output=True,text=True,timeout=20)
        assert denied.returncode!=0 and not Path('/etc/toddy-after-logout-proof.conf').exists(),'Background IPC retained a session grant after logout'
        passed('session-only-grant-refuses-no-session-after-logout')
        run(['/usr/bin/python3','/usr/lib/toddy/executor/policy.py','revoke','--uid',str(uid)])
        run(['systemctl','stop','toddy-executor.service'])
        run(['dpkg','--remove','toddy-executor'])
        assert not Path('/usr/lib/toddy/executor/owner_policy.py').exists()
        assert not run(['dpkg','--audit']).stdout.strip()
        passed('native-package-remove-preserves-private-state-for-recovery')
        secret=None
        run(['loginctl','terminate-user',str(uid)])
        run(['systemctl','stop','user@'+str(uid)+'.service'])
        until=time.monotonic()+10
        while time.monotonic()<until and run(['ps','-u',str(uid),'-o','pid='],check=False).stdout.strip():time.sleep(.1)
        assert not run(['ps','-u',str(uid),'-o','pid='],check=False).stdout.strip(),'Ephemeral user processes remain after session/user-manager termination'
        run(['userdel','-r',username])
        report['all_selected_exits_zero']=True;emit(report)
    finally:
        os.close(fd)
        try:os.kill(pid,signal.SIGKILL)
        except ProcessLookupError:pass


if __name__=='__main__':
    try:main()
    except Exception as error:
        emit({'all_selected_exits_zero':False,'error_type':type(error).__name__,'error':str(error)})
        raise

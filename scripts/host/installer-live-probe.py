#!/usr/bin/python3
"""Trusted disposable live qualification root controller; never installed."""
import base64,fcntl,hashlib,json,os,pwd,resource,select,signal,sqlite3,stat,subprocess,sys,time
from pathlib import Path

BASE=Path('/run/toddy-installer-qualification')
SOURCE=BASE/'media/source'
PROFILE=globals().get('QUALIFICATION_PROFILE','standard')
assert PROFILE in ('standard','phase2-mvp-preinstalled-v1')
MVP=PROFILE=='phase2-mvp-preinstalled-v1'
INPUTS=Path('/sources/stage/toddy-mvp-installer-native-inputs' if MVP else '/sources/stage/toddy-installer-native-inputs')
ENTRY='/opt/toddy-build/scripts/build/phase2/'+('mvp_installer_qualification.py' if MVP else 'installer_qualification.py')
SERIAL='TODDY-INSTALL-P2-1'
PORT=Path('/dev/virtio-ports/io.toddy.installer.control')
CHILD=None;CANCEL=None;REVIEW=None;EXECUTED=False


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def command(argv):return subprocess.check_output(argv,text=True,timeout=30).strip()
def write(path,data):
    with Path(path).open('xb') as stream:os.fchmod(stream.fileno(),0o600);stream.write(data);stream.flush();os.fsync(stream.fileno())
def sealed(data):
    fd=os.memfd_create('toddy-install-review',os.MFD_ALLOW_SEALING|os.MFD_CLOEXEC);os.fchmod(fd,0o600);os.write(fd,data);os.lseek(fd,0,0)
    fcntl.fcntl(fd,fcntl.F_ADD_SEALS,fcntl.F_SEAL_WRITE|fcntl.F_SEAL_GROW|fcntl.F_SEAL_SHRINK|fcntl.F_SEAL_SEAL);return fd


def prepare(expected):
    assert os.getuid()==os.geteuid()==0 and os.uname().release=='7.1.8-toddy'
    assert hasattr(sqlite3.Connection,'serialize')
    resource.setrlimit(resource.RLIMIT_CORE,(0,0));os.umask(0o077)
    assert 'toddy.live' in Path('/proc/cmdline').read_text().split()
    assert command(['/usr/bin/systemd-detect-virt','--vm']) in ('qemu','kvm')
    assert 'ID=toddy' in Path('/etc/os-release').read_text().splitlines()
    BASE.mkdir(mode=0o700);(BASE/'media').mkdir(mode=0o700)
    node=Path('/dev/disk/by-id/virtio-TODDY-INSTALL-DATA').resolve(strict=True)
    subprocess.run(['/usr/bin/mount','-t','iso9660','-o','ro,nosuid,nodev,noexec',str(node),str(BASE/'media')],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    descriptor=BASE/'media/snapshot.json';assert sha(descriptor)==expected
    value=json.loads(descriptor.read_bytes());assert value['kind']=='native-installer-qualification-snapshot-v1'
    assert (value.get('delivery_class')==PROFILE and value.get('g2_eligible') is False) if MVP else 'delivery_class' not in value
    expected=set(value['files'])|{'snapshot.json'};observed=set();directories=set()
    for base,children,leaves in os.walk(BASE/'media',followlinks=False):
        for leaf in children:
            directory=Path(base)/leaf;assert directory.resolve()==directory;directories.add(directory.relative_to(BASE/'media').as_posix())
        for leaf in leaves:observed.add((Path(base)/leaf).relative_to(BASE/'media').as_posix())
    assert observed==expected
    assert directories=={parent.as_posix() for name in expected for parent in Path(name).parents if parent.as_posix()!='.'}
    for path,digest in value['files'].items():
        file=BASE/'media'/path;info=file.lstat();assert '..' not in Path(path).parts and not Path(path).is_absolute() and file.resolve()==file and stat.S_ISREG(info.st_mode) and info.st_uid==info.st_gid==0 and info.st_nlink==1 and not info.st_mode&0o022 and sha(file)==digest
    Path('/opt').mkdir(mode=0o755,exist_ok=True)
    assert Path('/opt').resolve()==Path('/opt') and not Path('/opt/toddy-build').exists()
    Path('/opt/toddy-build').mkdir(mode=0o755)
    subprocess.run(['/usr/bin/mount','--bind',str(SOURCE),'/opt/toddy-build'],check=True)
    subprocess.run(['/usr/bin/mount','-o','remount,bind,ro,nosuid,nodev,noexec','/opt/toddy-build'],check=True)
    INPUTS.mkdir(mode=0o700,parents=True)
    (INPUTS/'payload').mkdir(mode=0o700)
    subprocess.run(['/usr/bin/mount','--bind',str(BASE/'media/inputs/payload'),str(INPUTS/'payload')],check=True)
    subprocess.run(['/usr/bin/mount','-o','remount,bind,ro,nosuid,nodev,noexec',str(INPUTS/'payload')],check=True)
    for name in ('policy.json','boot-profile.json','generated-entries.json','expected-image-manifest.json'):write(INPUTS/name,(BASE/'media/inputs'/name).read_bytes())
    # Source qualification must exercise exactly the installed runtime bytes.
    for relative,path in value['installed_runtime'].items():
        assert sha(SOURCE/relative)==sha(path)==value['files']['source/'+relative]
    for name,digest in value['installed_manifests'].items():assert sha('/usr/share/doc/'+name+'/source-manifest.json')==digest
    sys.path.insert(0,'/opt/toddy-build');sys.path.insert(0,'/opt/toddy-build/scripts/build/phase2')
    import installer_qualification as harness
    import runtime.installer.live_session as live
    deadline=time.monotonic()+240
    while True:
        try:
            live.authorize_live_owner(1000)
            assert pwd.getpwnam('toddy-live').pw_uid==1000
            assert subprocess.run(['/usr/bin/pgrep','-u','1000','-x','gnome-shell'],stdout=subprocess.DEVNULL).returncode==0
            break
        except (ValueError,AssertionError,FileNotFoundError):
            if time.monotonic()>deadline:raise
            time.sleep(1)
    if MVP:
        from mvp_installer_qualification import MVPInputs
        inputs=MVPInputs()
    else:inputs=harness.NativeInputs()
    assert inputs.descriptor==value['descriptor']
    return value


def launch_assistant():
    from runtime.installer.live_session import authorize_live_owner
    authorize_live_owner(1000)
    owner=pwd.getpwnam('toddy-live')
    assert (owner.pw_uid,owner.pw_gid,owner.pw_dir)==(1000,1000,'/home/toddy-live')
    environment={'PATH':'/usr/bin:/usr/sbin','HOME':owner.pw_dir,'USER':'toddy-live','LOGNAME':'toddy-live',
        'XDG_RUNTIME_DIR':'/run/user/1000','DBUS_SESSION_BUS_ADDRESS':'unix:path=/run/user/1000/bus',
        'WAYLAND_DISPLAY':'wayland-0','XDG_SESSION_TYPE':'wayland','LANG':'en_US.UTF-8'}
    child=subprocess.Popen(['/usr/bin/toddy'],user=1000,group=1000,extra_groups=[],cwd=owner.pw_dir,
        env=environment,close_fds=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    return {'state':'assistant-launch-requested','live_uid':1000,'launcher':'/usr/bin/toddy','pid':child.pid,
        'window_verified':False,'native_GUI_acceptance':False,'model_or_provider_activated':False}


def journal_snapshot():
    path=Path('/var/lib/toddy/installer-qualification/operations.sqlite')
    if not path.exists():return None
    info=path.lstat()
    assert path.resolve()==path and (info.st_mode,info.st_uid,info.st_gid,info.st_nlink)==(stat.S_IFREG|0o600,0,0,1)
    source=sqlite3.connect('file:'+str(path)+'?mode=ro',uri=True);target=sqlite3.connect(':memory:')
    try:
        source.backup(target);data=target.serialize();assert len(data)<=1024**2
        tables={row[0] for row in target.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        assert tables=={'operations','receipts'}
        return {'sha256':hashlib.sha256(data).hexdigest(),'database_b64':base64.b64encode(data).decode()}
    finally:target.close();source.close()


def main(expected):
    global CHILD,CANCEL,REVIEW,EXECUTED
    for number in (signal.SIGTERM,signal.SIGINT,signal.SIGHUP):signal.signal(number,lambda *_:(_ for _ in ()).throw(SystemExit(1)))
    value=prepare(expected);deadline=time.monotonic()+60
    while not PORT.exists():
        if time.monotonic()>deadline:raise TimeoutError('private-port-unavailable')
        time.sleep(.1)
    with PORT.open('r+b',buffering=0) as wire:
        def reply(data):wire.write(json.dumps(data,sort_keys=True,separators=(',',':')).encode()+b'\n')
        reply({'state':'live-root-qualification-ready','boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'snapshot_sha256':expected,'live_owner':'toddy-live','root_autologin':False})
        seen=set();buffer=b'';last=None;gui=None;last_journal=None;observed_at=0
        while True:
            if time.monotonic()-observed_at>1:
                observed_at=time.monotonic();journal=journal_snapshot()
                if journal and journal['sha256']!=last_journal:
                    reply({'event':'actual-journal-snapshot',**journal});last_journal=journal['sha256']
            if CHILD is not None and CHILD.poll() is not None:
                journal=journal_snapshot()
                if journal and journal['sha256']!=last_journal:reply({'event':'actual-journal-snapshot',**journal});last_journal=journal['sha256']
                stdout,stderr=CHILD.communicate();result=json.loads(stdout) if CHILD.returncode==0 and len(stdout)<=65536 else {'state':'failed-reconciliation-required'}
                last={'exit':CHILD.returncode,'result':result};CHILD=None;os.close(CANCEL);CANCEL=None
                reply({'event':'execute-ended',**last})
            if not select.select([wire],[],[],.2)[0]:continue
            data=wire.read(65536)
            if not data:
                if CANCEL is not None:os.close(CANCEL);CANCEL=None
                if CHILD is not None:CHILD.wait(timeout=1900)
                return
            buffer+=data
            assert len(buffer)<=65536
            if b'\n' not in buffer:continue
            line,buffer=buffer.split(b'\n',1);request=json.loads(line);identity=request.pop('request_id')
            assert isinstance(identity,str) and len(identity)<=64 and identity not in seen;seen.add(identity)
            action=request.pop('action');result={}
            if action=='review':
                assert not request.keys()-{'options'} and CHILD is None and REVIEW is None and not EXECUTED
                request={'device':str(Path('/dev/disk/by-id/virtio-'+SERIAL).resolve(strict=True)),'options':request['options']}
                fd=sealed(json.dumps(request).encode())
                try:raw=subprocess.check_output(['/usr/bin/python3','-I',ENTRY,'review','--options-fd',str(fd),'--serial',SERIAL],pass_fds=(fd,),stderr=subprocess.DEVNULL,timeout=60)
                finally:os.close(fd)
                assert len(raw)<=65536;REVIEW=json.loads(raw);write(BASE/'review.json',raw);result=REVIEW
            elif action=='execute':
                assert set(request)=={'confirm','password'} and REVIEW is not None and not EXECUTED and CHILD is None
                assert request['confirm']==REVIEW['plan']['plan_sha256']
                secret=request.pop('password').encode();line=b'';assert 12<=len(secret)<=1024 and not any(byte in secret for byte in (b'\n',b'\r',b'\x00'))
                plan=sealed(json.dumps(REVIEW['plan']).encode());credential,writer=os.pipe();cancel,CANCEL=os.pipe()
                os.write(writer,secret);os.close(writer);secret=None;request.clear();EXECUTED=True
                try:CHILD=subprocess.Popen(['/usr/bin/python3','-I',ENTRY,'execute','--plan-fd',str(plan),'--credential-fd',str(credential),'--cancel-fd',str(cancel),'--confirm',REVIEW['plan']['plan_sha256'],'--serial',SERIAL],pass_fds=(plan,credential,cancel),stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                finally:
                    for fd in (plan,credential,cancel):os.close(fd)
                result={'state':'execute-dispatched','canonical_result_pending':True}
            elif action=='cancel':
                assert not request
                if CANCEL is not None:os.write(CANCEL,b'1')
                result={'state':'cancel-requested','safe_boundary_result_pending':CHILD is not None}
            elif action=='status':
                assert not request;result={'running':CHILD is not None,'execute_started':EXECUTED,'last':last}
            elif action=='assistant-launch':
                assert not request and CHILD is None
                result=launch_assistant()
            elif action=='gui':
                assert not request and CHILD is None and gui is None
                gui=subprocess.Popen(['/usr/bin/python3','-I',ENTRY,'gui','--uid','1000','--display','wayland-0'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
                result={'state':'qualification-gui-requested','disk_write_enabled':False,'native_GUI_acceptance':False}
            elif action=='collect':
                assert not request and CHILD is None and last is not None and last['exit']==0 and last['result'].get('state')=='completed'
                raw=subprocess.check_output(['/usr/bin/python3','-I',*([ENTRY,'collect'] if MVP else ['/opt/toddy-build/scripts/build/phase2/installer_collect.py']),'--review',str(BASE/'review.json'),'--stream'],stderr=subprocess.DEVNULL,timeout=60)
                assert len(raw)<=12*1024**2;collected=json.loads(raw)
                assert collected['state']=='actual-evidence-read-only-stream' and len(collected['files'])==10
                result={'state':'actual-evidence-collected','files':collected['files']}
            elif action=='finish':
                assert not request and CHILD is None
                reply({'request_id':identity,'result':{'state':'poweroff-requested','installation_accepted':False}})
                subprocess.run(['/usr/bin/systemctl','poweroff'],check=True);return
            else:raise ValueError('fixed-qualification-action-required')
            reply({'request_id':identity,'result':result})


if __name__=='__main__':
    try:main(EXPECTED_SNAPSHOT_SHA256)
    except BaseException:
        if CANCEL is not None:
            try:os.close(CANCEL)
            except OSError:pass
        if CHILD is not None:
            try:CHILD.wait(timeout=1900)
            except subprocess.TimeoutExpired:pass
        # Never print request, password, native stderr or exception value.
        print('TODDY_INSTALLER_QUALIFICATION_STOPPED: inspect actual state; no automatic retry',flush=True)
        raise SystemExit(1)

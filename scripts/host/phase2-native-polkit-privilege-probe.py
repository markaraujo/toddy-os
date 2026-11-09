"""Run five unchanged Polkit drivers with native user/mount namespaces."""
import base64,hashlib,json,os,re,subprocess,zlib,shutil,secrets,pty,select,signal,time,pwd
from pathlib import Path

def output(args):return subprocess.check_output(args,text=True,timeout=15).strip()
def digest(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
    assert os.geteuid()==0 and os.uname().release=='7.1.8-toddy'
    assert Path('/proc/1/comm').read_text().strip()=='systemd'
    assert output(['systemd-detect-virt','--vm']) in ['kvm','qemu']
    device=output(['findmnt','-n','-o','SOURCE','/']);assert re.fullmatch('/dev/[a-z0-9]+',device)
    parent=output(['lsblk','-ndo','PKNAME',device]);assert re.fullmatch('[a-z0-9]+',parent)
    assert output(['lsblk','-dnro','SERIAL','/dev/'+parent])=='TODDY-BOOT-TEST'
    assert output(['blkid','-s','LABEL','-o','value',device])=='TODDY_LFS'
    assert output(['findmnt','-n','-o','FSTYPE','/sys/fs/cgroup'])=='cgroup2'
    fixture=Path('/sources/phase2/native-fixtures/polkit-suite-1');accepted=json.loads((fixture/'accepted.json').read_text())
    def verify():
        for name,row in accepted['files'].items():
            p=Path('/')/name
            if 'sha256' in row:assert not p.is_symlink() and digest(p)==row['sha256']
            else:assert p.is_symlink() and str(p.readlink())==row['symlink']
    verify();stage=Path('/')/accepted['work']/'stage'
    assert not Path('/usr/bin/pkexec').exists()
    for name in ['usr','etc']:
        if (stage/name).exists():shutil.copytree(stage/name,Path('/')/name,symlinks=True,dirs_exist_ok=True)
    for p in [*Path('/usr/lib/polkit-1').rglob('*'),*Path('/etc/polkit-1').rglob('*')]:
        os.chown(p,0,0,follow_symlinks=False)
    helpers=[]
    for name in ['usr/bin/pkexec','usr/lib/polkit-1/polkit-agent-helper-1']:
        p=Path('/')/name;assert digest(p)==digest(stage/name);os.chown(p,0,0);p.chmod(0o4755)
        helpers.append({'path':'/'+name,'sha256':digest(p),'uid':0,'gid':0,'mode':'4755'})
    subprocess.run(['ldconfig'],check=True)
    subprocess.run(['useradd','-r','-U','-M','-s','/usr/bin/nologin','polkitd'],check=True,capture_output=True)
    daemon=pwd.getpwnam('polkitd');assert daemon.pw_uid!=0
    directory=Path('/etc/polkit-1/rules.d');os.chown(directory,0,daemon.pw_gid);directory.chmod(0o750)
    name='toddy-polkit-probe';uid=12345
    assert not any(row.split(':')[0]==name or row.split(':')[2]==str(uid) for row in Path('/etc/passwd').read_text().splitlines())
    subprocess.run(['useradd','-M','-U','-u',str(uid),'-s','/bin/sh',name],capture_output=True,check=True)
    password=secrets.token_urlsafe(32)
    result=subprocess.run(['chpasswd','-c','YESCRYPT'],input=name+':'+password+'\n',text=True,capture_output=True,timeout=20)
    assert result.returncode==0,'Ephemeral password creation failed; no output retained'
    Path('/etc/pam.d/polkit-auth').write_text('auth required pam_unix.so\naccount required pam_unix.so\npassword required pam_deny.so\nsession required pam_deny.so\n')
    actiondir=Path('/usr/share/polkit-1/actions');actiondir.mkdir(exist_ok=True)
    (actiondir/'org.toddy.test.policy').write_text('<?xml version="1.0"?><!DOCTYPE policyconfig PUBLIC "-//freedesktop//DTD PolicyKit Policy Configuration 1.0//EN" "http://www.freedesktop.org/standards/PolicyKit/1/policyconfig.dtd"><policyconfig>'+''.join('<action id="org.toddy.test.'+a+'"><description>Native test</description><message>Authenticate native test</message><defaults><allow_any>no</allow_any><allow_inactive>no</allow_inactive><allow_active>no</allow_active></defaults></action>' for a in ['allow','deny','challenge'])+'</policyconfig>')
    rules=Path('/etc/polkit-1/rules.d/00-toddy-native-test.rules')
    rules.write_text('polkit.addAdminRule(function(action, subject) { return ["unix-user:'+name+'"]; });\npolkit.addRule(function(action, subject) { if(subject.user != "'+name+'") return null; if(action.id == "org.toddy.test.allow") return polkit.Result.YES; if(action.id == "org.toddy.test.deny") return polkit.Result.NO; if(action.id == "org.toddy.test.challenge") return polkit.Result.AUTH_ADMIN; });\n')
    subprocess.run(['dbus-send','--system','--type=method_call','--print-reply','--dest=org.freedesktop.DBus','/','org.freedesktop.DBus.ReloadConfig'],check=True,capture_output=True)
    subprocess.run(['systemctl','daemon-reload'],check=True)
    subprocess.run(['systemctl','start','polkit-agent-helper.socket','polkit.service'],check=True,timeout=30)
    assert output(['systemctl','is-active','polkit.service'])=='active'
    owner1=output(['busctl','--system','call','org.freedesktop.DBus','/org/freedesktop/DBus','org.freedesktop.DBus','GetNameOwner','s','org.freedesktop.PolicyKit1'])
    runs=[]
    def decision(label,action,expected):
        code='import os;from pathlib import Path;p=os.getpid();start=Path("/proc/self/stat").read_text().split()[21];os.execv("/usr/bin/pkcheck",["pkcheck","--action-id",'+repr(action)+',"--process",f"{p},{start},{os.getuid()}"])'
        r=subprocess.run(['python3','-c',code],user=uid,group=uid,extra_groups=[],env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8'},capture_output=True,timeout=15)
        assert r.returncode==expected,'Authorization decision mismatch: '+label
        runs.append({'name':label,'exit':r.returncode,'expected':expected})
    decision('allow-kernel-peer','org.toddy.test.allow',0)
    decision('explicit-deny','org.toddy.test.deny',1)
    decision('challenge-without-agent-refused','org.toddy.test.challenge',1)
    def authenticate(label,secret,expect_success=False,cancel=False):
        child,fd=pty.fork()
        if child==0:
            os.setgroups([]);os.setgid(uid);os.setuid(uid)
            os.environ.clear();os.environ.update(PATH='/usr/bin:/usr/sbin',LC_ALL='C.UTF-8',HOME='/tmp',TERM='dumb')
            os.execv('/usr/bin/pkexec',['pkexec','/usr/bin/id','-u'])
        os.set_blocking(fd,False);tail=b'';transcript=b'';prompts=0;status=None;deadline=time.monotonic()+35
        try:
            while time.monotonic()<deadline:
                if select.select([fd],[],[],0.1)[0]:
                    try:data=os.read(fd,65536)
                    except OSError:data=b''
                    transcript+=data;tail=(tail+data)[-4096:]
                    if re.search(rb'[Pp]assword: *$',tail):
                        prompts+=1;tail=b''
                        if cancel:os.kill(child,signal.SIGINT)
                        else:os.write(fd,secret.encode()+b'\n')
                waited,raw_status=os.waitpid(child,os.WNOHANG)
                if waited:status=os.waitstatus_to_exitcode(raw_status);break
            if status is None:
                os.kill(child,signal.SIGKILL);os.waitpid(child,0)
                raise AssertionError('Authentication deadline, never success: '+label)
            assert prompts>0,'No real PAM prompt observed: '+label
            if expect_success:assert status==0 and re.search(rb'(?m)^0\r?$',transcript),'Expected root execution: '+label
            else:assert status!=0,'Unexpected privileged execution: '+label
            # Never retain raw tty traffic or secrets (even on failures).
            runs.append({'name':label,'exit':status,'expected_authenticated':expect_success,'pam_prompts':prompts,'raw_tty_retained':False})
        finally:os.close(fd)
    authenticate('correct-password-root-execution',password,True)
    authenticate('wrong-password-refused',secrets.token_urlsafe(32))
    authenticate('stop-at-authentication',password,cancel=True)
    authenticate('recovery-after-stop',password,True)
    subprocess.run(['systemctl','stop','polkit.service'],check=True,timeout=20)
    assert output(['systemctl','is-active','polkit-agent-helper.socket'])=='active'
    subprocess.run(['systemctl','start','polkit.service'],check=True,timeout=30)
    owner2=output(['busctl','--system','call','org.freedesktop.DBus','/org/freedesktop/DBus','org.freedesktop.DBus','GetNameOwner','s','org.freedesktop.PolicyKit1']);assert owner2!=owner1
    decision('daemon-reconnect-recovery','org.toddy.test.allow',0)
    rules.write_text('polkit.addRule(function(action, subject) { if(subject.user == "'+name+'") return polkit.Result.NO; });\n')
    # Deterministic service restart applies the changed independent policy.
    subprocess.run(['systemctl','restart','polkit.service'],check=True,timeout=30)
    decision('revoked-policy-replay-refused','org.toddy.test.allow',1)
    subprocess.run(['systemctl','stop','polkit.service','polkit-agent-helper.socket'],check=True,timeout=20)
    password=None;subprocess.run(['userdel',name],capture_output=True,check=True)
    assert not any(row.startswith(name+':') for row in Path('/etc/passwd').read_text().splitlines())
    verify()
    raw=json.dumps({'scope':'Real Polkit system-bus, exact privileged helper/PAM password/challenge/refusal/Stop/restart/revocation in disposable native fixture only; package promotion and GNOME UI still pending','kernel':os.uname().release,'fixture_manifest_sha256':digest(fixture/'accepted.json'),'unchanged_fixture_files':len(accepted['files']),'helpers':helpers,'runs':runs,'distinct_daemon_bus_owners':True,'ephemeral_account_removed':True,'secrets_retained':False},sort_keys=True).encode()
    success=True
    encoded=base64.b64encode(zlib.compress(raw,9)).decode();chunks=[encoded[i:i+1024] for i in range(0,len(encoded),1024)]
    for i,chunk in enumerate(chunks):print('TODDY_B02_RUNTIME_DATA',i,chunk,flush=True)
    print('TODDY_B02_RUNTIME_RESULT',json.dumps({'kernel':os.uname().release,'all_selected_exits_zero':success,'report_sha256':hashlib.sha256(raw).hexdigest(),'chunks':len(chunks)}),flush=True)
    assert success,'Original native failures retained; not qualified'
if __name__=='__main__':
    try:main()
    except Exception as error:
        print('TODDY_B02_RUNTIME_FAIL',type(error).__name__,str(error),flush=True)
        raise

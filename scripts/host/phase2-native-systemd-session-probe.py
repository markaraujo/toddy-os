"""Cold native updated PID1, PAMName and real logind/user-bus session recovery."""
import base64,hashlib,json,os,re,select,stat,subprocess,time,zlib
from pathlib import Path

def output(args):return subprocess.check_output(args,text=True,timeout=25).strip()
def digest(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def command(args,**kw):return subprocess.run(args,capture_output=True,text=True,timeout=30,**kw)
def wait_for(test,seconds=20):
    until=time.monotonic()+seconds
    while time.monotonic()<until:
        value=test()
        if value:return value
        time.sleep(0.2)
    raise AssertionError('Native state postcondition did not arrive within its bounded deadline')
def main():
    assert os.geteuid()==0 and os.uname().release=='7.1.8-toddy'
    assert Path('/proc/1/comm').read_text().strip()=='systemd'
    assert output(['systemd-detect-virt','--vm']) in ['kvm','qemu']
    device=output(['findmnt','-n','-o','SOURCE','/']);assert re.fullmatch('/dev/[a-z0-9]+',device)
    parent=output(['lsblk','-ndo','PKNAME',device]);assert re.fullmatch('[a-z0-9]+',parent)
    assert output(['lsblk','-dnro','SERIAL','/dev/'+parent])=='TODDY-BOOT-TEST'
    assert output(['blkid','-s','LABEL','-o','value',device])=='TODDY_LFS'
    assert output(['findmnt','-n','-o','FSTYPE','/sys/fs/cgroup'])=='cgroup2'
    fixture=Path('/sources/phase2/native-fixtures/systemd-session-1');accepted=json.loads((fixture/'accepted.json').read_text())
    for name,sha in accepted['artifacts'].items():assert digest(fixture/name)==sha
    for name,sha in accepted['installed_artifacts'].items():assert digest(Path(name))==sha
    assert digest(Path('/proc/1/exe'))==accepted['installed_artifacts']['/usr/lib/systemd/systemd']
    features=output(['systemctl','show','--property=Features','--value']);assert '+PAM' in features
    assert output(['dpkg-query','-W','-f=${Status} ${Version}','systemd'])=='install ok installed 261.2-1+toddy3'
    subprocess.run(['systemctl','start','dbus.service','systemd-logind.service'],check=True,timeout=30)
    assert output(['systemctl','is-active','dbus.service'])==output(['systemctl','is-active','systemd-logind.service'])=='active'
    uid=12345;user='toddy-session-probe';home=Path('/home')/user
    assert not home.exists() and not any(row.split(':')[0]==user or row.split(':')[2]==str(uid) for row in Path('/etc/passwd').read_text().splitlines())
    subprocess.run(['useradd','-m','-U','-u',str(uid),'-s','/bin/bash',user],check=True,capture_output=True)
    # These policies exist only in the fresh disposable child. No authentication
    # password is needed: only root can request these User=/PAMName= units.
    policies=[]
    for name,module in [('toddy-pam-allow','pam_permit.so'),('toddy-pam-deny','pam_deny.so')]:
        p=Path('/etc/pam.d')/name;assert not p.exists();p.write_text(''.join(f'{group} required {module}\n' for group in ['auth','account','password','session']));policies.append(p)
    runs=[{'name':'cold-boot-new-PID1-PAM','exit':0,'pid1_sha256':digest(Path('/proc/1/exe')),'features':features,'dbus':'active','logind':'active'}]
    live='toddy-pam-live.service'
    r=command(['systemd-run','--quiet','--unit='+live,'--property=User='+str(uid),'--property=PAMName=toddy-pam-allow','/usr/bin/sleep','60']);assert r.returncode==0,{'case':'PAMName-live','exit':r.returncode,'stderr':r.stderr}
    assert output(['systemctl','show',live,'--property=PAMName','--value'])=='toddy-pam-allow'
    assert output(['systemctl','is-active',live])=='active'
    cgroup=output(['systemctl','show',live,'--property=ControlGroup','--value']);assert cgroup.startswith('/system.slice/') and '..' not in cgroup
    subprocess.run(['systemctl','stop',live],check=True,timeout=20)
    def no_live_processes():
        p=Path('/sys/fs/cgroup')/cgroup.lstrip('/')/'cgroup.procs'
        return not p.exists() or not p.read_text().strip()
    wait_for(no_live_processes)
    runs.append({'name':'PAMName-allow-and-stop-cleanup','exit':0,'pam_name':'toddy-pam-allow','service_cgroup_empty':True})
    deny='toddy-pam-denied.service'
    r=command(['systemd-run','--wait','--pipe','--unit='+deny,'--property=User='+str(uid),'--property=PAMName=toddy-pam-deny','/usr/bin/true']);assert r.returncode!=0
    status=output(['systemctl','show',deny,'--property=ExecMainStatus','--value']);assert status=='224',{'case':'PAMName-deny','actual_status':status,'runner_exit':r.returncode,'stderr':r.stderr}
    subprocess.run(['systemctl','reset-failed',deny],check=True,timeout=15)
    runs.append({'name':'PAMName-account-denied','exit':0,'expected_exec_status':224,'actual_exec_status':int(status)})
    r=command(['systemd-run','--wait','--pipe','--collect','--unit=toddy-pam-recovered','--property=User='+str(uid),'--property=PAMName=toddy-pam-allow','/usr/bin/id','-u']);assert r.returncode==0 and r.stdout.strip()==str(uid)
    runs.append({'name':'PAMName-service-recovery-as-user','exit':0,'actual_uid':uid})
    policy=Path('/run/toddy-session-policy');policy.mkdir(mode=0o755)
    (policy/'toddy-session').write_text('account required pam_unix.so\nsession required pam_systemd.so\n')
    cycles=[]
    for cycle in [1,2]:
        client=subprocess.Popen([str(fixture/'session-consumer'),str(policy),user],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8'})
        assert select.select([client.stdout],[],[],30)[0],'No PAM ready result before deadline'
        line=client.stdout.readline();assert line,{'case':'PAM-session-ready','client_exit':client.poll(),'stderr':client.stderr.read() if client.poll() is not None else 'client alive'}
        ready=json.loads(line);assert ready['phase']=='ready',ready
        sid=ready['session_id'];assert isinstance(sid,str) and re.fullmatch('[A-Za-z0-9]+',sid)
        runtime=Path('/run/user')/str(uid);assert ready['runtime_dir']==str(runtime) and ready['session_type']=='tty'
        st=runtime.stat();assert st.st_uid==uid and stat.S_IMODE(st.st_mode)==0o700
        props=dict(row.split('=',1) for row in output(['loginctl','show-session',sid,'--property=User','--property=Name','--property=Leader','--property=Class','--property=Type','--property=State','--property=Service','--property=Seat']).splitlines())
        assert props['User']==str(uid) and props['Name']==user and props['Leader']==str(client.pid) and props['Class']=='user' and props['Type']=='tty' and props['Service']=='toddy-session'
        assert props['State'] in ['active','online']
        wait_for(lambda: command(['systemctl','is-active','user@'+str(uid)+'.service']).stdout.strip()=='active')
        wait_for(lambda: (runtime/'bus').is_socket())
        env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':str(home),'USER':user,'LOGNAME':user,'XDG_RUNTIME_DIR':str(runtime),'DBUS_SESSION_BUS_ADDRESS':'unix:path='+str(runtime/'bus')}
        bus=command(['busctl','--user','call','org.freedesktop.DBus','/org/freedesktop/DBus','org.freedesktop.DBus','GetId'],user=uid,group=uid,extra_groups=[],env=env);assert bus.returncode==0 and re.fullmatch('s "[0-9a-f]+"\n?',bus.stdout),{'case':'user-bus','exit':bus.returncode,'stderr':bus.stderr}
        target=command(['systemctl','--user','is-active','default.target'],user=uid,group=uid,extra_groups=[],env=env);assert target.returncode==0 and target.stdout.strip()=='active'
        out,err=client.communicate('\n',timeout=25);assert client.returncode==0
        closed=json.loads(out.strip());assert closed=={'phase':'closed','close':0,'end':0}
        subprocess.run(['loginctl','terminate-user',str(uid)],check=True,timeout=25)
        wait_for(lambda: command(['systemctl','is-active','user@'+str(uid)+'.service']).stdout.strip() in ['inactive','unknown'])
        wait_for(lambda: not runtime.exists())
        wait_for(lambda: command(['loginctl','show-session',sid]).returncode!=0)
        cycles.append({'cycle':cycle,'pam_open_exit':0,'session':props,'runtime_owner_uid':st.st_uid,'runtime_mode':'0700','user_manager':'active','user_default_target':'active','user_bus_get_id_exit':0,'bus_id_sha256':hashlib.sha256(bus.stdout.encode()).hexdigest(),'pam_close_exit':closed['close'],'pam_end_exit':closed['end'],'client_stderr_sha256':hashlib.sha256(err.encode()).hexdigest(),'session_and_runtime_removed':True})
    assert cycles[0]['bus_id_sha256']!=cycles[1]['bus_id_sha256'],'Recovery must have a genuinely new user bus'
    assert home.is_dir() and not home.is_symlink() and home.stat().st_uid==uid
    subprocess.run(['userdel','-r',user],capture_output=True,check=True,timeout=20)
    for p in policies:p.unlink()
    assert not home.exists() and not any(row.startswith(user+':') for row in Path('/etc/passwd').read_text().splitlines())
    for name,sha in accepted['artifacts'].items():assert digest(fixture/name)==sha
    for name,sha in accepted['installed_artifacts'].items():assert digest(Path(name))==sha
    raw=json.dumps({'scope':'Actual updated Systemd261.2 cold boot/PAMName allow-deny-stop-recovery and two real PAM/logind/user-manager/user-bus cycles; no GDM/GNOME/physical acceptance','kernel':os.uname().release,'pid1':'systemd','fixture_manifest_sha256':digest(fixture/'accepted.json'),'runs':runs,'session_cycles':cycles,'unchanged_installed_artifacts':len(accepted['installed_artifacts']),'unchanged_fixture_files':len(accepted['artifacts']),'ephemeral_account_removed':True,'passwords_or_tokens_used':False},sort_keys=True).encode()
    encoded=base64.b64encode(zlib.compress(raw,9)).decode();chunks=[encoded[i:i+1024] for i in range(0,len(encoded),1024)]
    for i,chunk in enumerate(chunks):print('TODDY_B02_RUNTIME_DATA',i,chunk,flush=True)
    print('TODDY_B02_RUNTIME_RESULT',json.dumps({'kernel':os.uname().release,'all_selected_exits_zero':True,'report_sha256':hashlib.sha256(raw).hexdigest(),'chunks':len(chunks)}),flush=True)
if __name__=='__main__':
    try:main()
    except Exception as error:
        print('TODDY_B02_RUNTIME_FAIL',type(error).__name__,str(error),flush=True)
        raise

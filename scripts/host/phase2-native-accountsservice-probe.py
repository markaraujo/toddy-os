"""Verify real native account permissions, credential changes and service recovery."""
import base64,hashlib,json,os,re,subprocess,zlib,shutil,secrets
from gi.repository import Gio,GLib
from pathlib import Path

def output(args):return subprocess.check_output(args,text=True,timeout=15).strip()
def digest(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
ACCOUNT_CLIENT='import json,re,sys\nfrom gi.repository import Gio,GLib\nrequest=json.load(sys.stdin);bus=Gio.bus_get_sync(Gio.BusType.SYSTEM,None)\nmethod=request[\'method\'];assert method in [\'SetRealName\',\'SetPassword\',\'SetIconFile\']\nsignature=\'(ss)\' if method==\'SetPassword\' else \'(s)\'\ntry:\n bus.call_sync(\'org.freedesktop.Accounts\',request[\'path\'],\'org.freedesktop.Accounts.User\',method,GLib.Variant(signature,tuple(request[\'values\'])),None,Gio.DBusCallFlags.NO_AUTO_START,15000,None)\n result={\'authorized\':True}\nexcept GLib.Error as error:\n result={\'authorized\':False,\'remote_error\':Gio.DBusError.get_remote_error(error),\'protected_read_failed\':error.message.endswith("reading file \'/etc/shadow\' failed"),\'permission_refused\':bool(re.search(\'permission|denied|not allowed|readable|access|ownership\',error.message,re.I))}\nrequest=None;print(json.dumps(result))\n'

def main():
    assert os.geteuid()==0 and os.uname().release=='7.1.8-toddy'
    assert Path('/proc/1/comm').read_text().strip()=='systemd'
    assert output(['systemd-detect-virt','--vm']) in ['kvm','qemu']
    device=output(['findmnt','-n','-o','SOURCE','/']);assert re.fullmatch('/dev/[a-z0-9]+',device)
    parent=output(['lsblk','-ndo','PKNAME',device]);assert re.fullmatch('[a-z0-9]+',parent)
    assert output(['lsblk','-dnro','SERIAL','/dev/'+parent])=='TODDY-BOOT-TEST'
    assert output(['blkid','-s','LABEL','-o','value',device])=='TODDY_LFS'
    assert output(['findmnt','-n','-o','FSTYPE','/sys/fs/cgroup'])=='cgroup2'
    fixture=Path('/sources/phase2/native-fixtures/accountsservice-1');accepted=json.loads((fixture/'accepted.json').read_text())
    def verify():
        for name,row in accepted['files'].items():
            p=Path('/')/name
            if 'sha256' in row:assert not p.is_symlink() and digest(p)==row['sha256']
            else:assert p.is_symlink() and str(p.readlink())==row['symlink']
    verify();stage=Path('/')/accepted['stage'];assert not Path('/usr/libexec/accounts-daemon').exists()
    for name in ['usr','etc','var']:
        if (stage/name).exists():shutil.copytree(stage/name,Path('/')/name,symlinks=True,dirs_exist_ok=True)
    subprocess.run(['ldconfig'],check=True)
    users=[('toddy-accounts-a',12345),('toddy-accounts-b',12346)]
    for name,uid in users:
        assert not any(r.split(':')[0]==name or r.split(':')[2]==str(uid) for r in Path('/etc/passwd').read_text().splitlines())
        subprocess.run(['useradd','-M','-U','-u',str(uid),'-d','/home/'+name,'-s','/bin/sh',name],check=True,capture_output=True)
    old_password=secrets.token_urlsafe(32);new_password=secrets.token_urlsafe(32)
    r=subprocess.run(['chpasswd','-c','YESCRYPT'],input=users[0][0]+':'+old_password+'\n'+users[1][0]+':'+new_password+'\n',capture_output=True,text=True,timeout=20)
    assert r.returncode==0,'Ephemeral password setup failed; no output retained'
    def shadow(name):return next(r.split(':')[1] for r in Path('/etc/shadow').read_text().splitlines() if r.startswith(name+':'))
    new_hash=shadow(users[1][0]);assert new_hash.startswith('$y$')
    subprocess.run(['dbus-send','--system','--type=method_call','--print-reply','--dest=org.freedesktop.DBus','/','org.freedesktop.DBus.ReloadConfig'],check=True,capture_output=True)
    subprocess.run(['systemctl','daemon-reload'],check=True)
    subprocess.run(['systemctl','start','systemd-logind.service','polkit.service','accounts-daemon.service'],check=True,timeout=30)
    assert output(['systemctl','is-active','accounts-daemon.service'])=='active'
    pid=int(output(['systemctl','show','-p','MainPID','--value','accounts-daemon.service']));assert pid>1
    assert [int(x) for x in next(s for s in Path('/proc/'+str(pid)+'/status').read_text().splitlines() if s.startswith('Uid:')).split()[1:]]==[0,0,0,0]
    service_env=Path('/proc/'+str(pid)+'/environ').read_bytes().split(b'\0');assert not any(any(v.startswith(n+b'=') for v in service_env) for n in [b'ROOTDIR',b'LD_PRELOAD',b'MOCK_PASSWD',b'MOCK_GROUP',b'MOCKLIBC_LD_PRELOAD'])
    assert Path('/proc/'+str(pid)+'/exe').resolve()==Path('/usr/libexec/accounts-daemon') and digest(Path('/usr/libexec/accounts-daemon'))==digest(stage/'usr/libexec/accounts-daemon')
    bus=Gio.bus_get_sync(Gio.BusType.SYSTEM,None)
    def call(dest,path,interface,method,params=None):
        return bus.call_sync(dest,path,interface,method,params,None,Gio.DBusCallFlags.NO_AUTO_START,15000,None).unpack()
    destination='org.freedesktop.Accounts';account_iface='org.freedesktop.Accounts.User'
    def user(uid):return call(destination,'/org/freedesktop/Accounts',destination,'FindUserById',GLib.Variant('(x)',(uid,)))[0]
    def properties(path):return call(destination,path,'org.freedesktop.DBus.Properties','GetAll',GLib.Variant('(s)',(account_iface,)))[0]
    def owner():return call('org.freedesktop.DBus','/org/freedesktop/DBus','org.freedesktop.DBus','GetNameOwner',GLib.Variant('(s)',(destination,)))[0]
    paths=[user(uid) for name,uid in users]
    for (name,uid),path in zip(users,paths):
        props=properties(path);assert props['Uid']==uid and props['UserName']==name and not props['SystemAccount']
    initial_owner=owner();runs=[{'name':'real-system-bus-user-lookup','expected_outcome_passed':True,'uids':[12345,12346]}]
    helper=Path('/run/toddy-accounts-client.py')
    helper.write_text(ACCOUNT_CLIENT);helper.chmod(0o644)
    def client(uid,request):
        r=subprocess.run(['python3',str(helper)],input=json.dumps(request),user=uid,group=uid,extra_groups=[],env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','PYTHONDONTWRITEBYTECODE':'1'},capture_output=True,text=True,timeout=20)
        assert r.returncode==0,'Native client failed, no credential output retained'
        return json.loads(r.stdout)
    result=client(12345,{'method':'SetRealName','path':paths[0],'values':['Toddy Native Owner']});assert result['authorized']
    assert properties(paths[0])['RealName']=='Toddy Native Owner' and next(r.split(':')[4] for r in Path('/etc/passwd').read_text().splitlines() if r.startswith(users[0][0]+':'))=='Toddy Native Owner'
    runs.append({'name':'own-real-name-and-actual-passwd-update','expected_outcome_passed':True})
    result=client(12346,{'method':'SetRealName','path':paths[0],'values':['Forbidden Change']});assert not result['authorized'] and result['remote_error']=='org.freedesktop.Accounts.Error.PermissionDenied'
    assert properties(paths[0])['RealName']=='Toddy Native Owner'
    runs.append({'name':'other-user-real-name-denied','expected_outcome_passed':True})
    before_hash=shadow(users[0][0])
    result=client(12346,{'method':'SetPassword','path':paths[0],'values':[new_hash,'fixture']});assert not result['authorized'] and result['remote_error']=='org.freedesktop.Accounts.Error.PermissionDenied' and shadow(users[0][0])==before_hash
    runs.append({'name':'other-user-password-denied-shadow-unchanged','expected_outcome_passed':True,'secrets_retained':False})
    icon_before=properties(paths[1])['IconFile']
    result=client(12346,{'method':'SetIconFile','path':paths[1],'values':['/etc/shadow']});assert not result['authorized'] and result['remote_error'] in ['org.freedesktop.Accounts.Error.Failed','org.freedesktop.Accounts.Error.PermissionDenied'] and (result['permission_refused'] or result['protected_read_failed']),json.dumps(result)
    refused=subprocess.run(['python3','-c',"import os,errno; fd=None\ntry: fd=os.open('/etc/shadow',os.O_RDONLY)\nexcept OSError as error: assert error.errno==errno.EACCES\nelse: os.close(fd); raise AssertionError('Protected file readable')"],user=12346,group=12346,extra_groups=[],capture_output=True,timeout=10)
    assert refused.returncode==0,'Direct peer protected-file refusal failed'
    assert properties(paths[1])['IconFile']==icon_before and not (Path('/var/lib/AccountsService/icons')/users[1][0]).exists()
    runs.append({'name':'protected-shadow-icon-read-refused','expected_outcome_passed':True,'no_icon_effect':True})
    call(destination,paths[0],account_iface,'SetPassword',GLib.Variant('(ss)',(new_hash,'fixture')))
    assert shadow(users[0][0])==new_hash and shadow(users[0][0])!=before_hash
    policy=Path('/run/toddy-accounts-pam');policy.mkdir(mode=0o755)
    (policy/'toddy-password').write_text('auth required /usr/lib/security/pam_unix.so\naccount required /usr/lib/security/pam_unix.so\n')
    def password_check(label,secret,valid):
        r=subprocess.run([str(Path('/')/accepted['pam_client']),str(policy),users[0][0]],input=secret+'\n',user=12345,group=12345,extra_groups=[],capture_output=True,text=True,timeout=20)
        assert r.returncode==0,'PAM client failed, no credential output retained'
        value=json.loads(r.stdout);assert value['start']==value['end']==0
        if valid:assert value['auth']==value['account']==value['credential']==0
        else:assert value['auth']!=0
        runs.append({'name':label,'expected_outcome_passed':True,'pam_result':value,'expected_authenticated':valid,'secrets_retained':False})
    password_check('administrator-password-change-real-PAM-new-password',new_password,True)
    password_check('old-password-after-change-refused',old_password,False)
    subprocess.run(['systemctl','stop','accounts-daemon.service'],check=True,timeout=20)
    assert not call('org.freedesktop.DBus','/org/freedesktop/DBus','org.freedesktop.DBus','NameHasOwner',GLib.Variant('(s)',(destination,)))[0]
    runs.append({'name':'stop-removes-bus-owner','expected_outcome_passed':True})
    subprocess.run(['systemctl','start','accounts-daemon.service'],check=True,timeout=30)
    assert owner()!=initial_owner and properties(user(12345))['RealName']=='Toddy Native Owner'
    password_check('restart-recovery-password-persists',new_password,True)
    runs.append({'name':'reconnect-new-owner-and-persistent-user-data','expected_outcome_passed':True})
    subprocess.run(['systemctl','stop','accounts-daemon.service'],check=True,timeout=20)
    for name,uid in users:subprocess.run(['userdel',name],check=True,capture_output=True)
    assert not any(any(r.startswith(name+':') for name,uid in users) for r in Path('/etc/passwd').read_text().splitlines())
    assert not any(any(r.startswith(name+':') for name,uid in users) for r in Path('/etc/shadow').read_text().splitlines())
    old_password=new_password=new_hash=before_hash=None;verify()
    success=all(r['expected_outcome_passed'] for r in runs)
    raw=json.dumps({'scope':'Real native AccountsService account/passwd/shadow/PAM/privilege/protected-file refusal/Stop/reconnect/persistence in disposable guest only; owned package/GDM/GUI still pending','kernel':os.uname().release,'fixture_manifest_sha256':digest(fixture/'accepted.json'),'unchanged_fixture_files':len(accepted['files']),'daemon_uid':0,'service_has_no_mock_environment':True,'upstream_service_hardening_used':True,'runs':runs,'ephemeral_accounts_removed':True,'secrets_retained':False},sort_keys=True).encode()
    encoded=base64.b64encode(zlib.compress(raw,9)).decode();chunks=[encoded[i:i+1024] for i in range(0,len(encoded),1024)]
    for i,chunk in enumerate(chunks):print('TODDY_B02_RUNTIME_DATA',i,chunk,flush=True)
    print('TODDY_B02_RUNTIME_RESULT',json.dumps({'kernel':os.uname().release,'all_selected_exits_zero':success,'report_sha256':hashlib.sha256(raw).hexdigest(),'chunks':len(chunks)}),flush=True)
    assert success,'Original native failures retained; not qualified'
if __name__=='__main__':
    try:main()
    except Exception as error:
        print('TODDY_B02_RUNTIME_FAIL',type(error).__name__,str(error),flush=True)
        raise

"""Real native PAM shadow/helper checks in a disposable boot-test overlay only."""
import base64,ctypes,hashlib,json,os,re,secrets,shutil,stat,subprocess,zlib
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
    assert output(['findmnt','-n','-o','FSTYPE','/'])=='ext4'
    assert output(['ip','-o','link','show']).count('\n')==0 and 'lo:' in output(['ip','-o','link','show'])
    fixture=Path('/sources/phase2/native-fixtures/pam-1');assert fixture.stat().st_uid==0
    accepted=json.loads((fixture/'accepted.json').read_text())
    for name,sha in accepted['artifacts'].items():assert digest(fixture/name)==sha
    stage=fixture/'stage';helper=Path('/usr/sbin/unix_chkpwd');assert not helper.exists()
    shutil.copy2(stage/'usr/sbin/unix_chkpwd',helper);os.chown(helper,0,0);helper.chmod(0o4755)
    assert digest(helper)==accepted['privileged_helper']['sha256']
    st=helper.stat();assert (st.st_uid,st.st_gid,stat.S_IMODE(st.st_mode))==(0,0,0o4755)
    assert 'nosuid' not in output(['findmnt','-n','-o','OPTIONS','/']).split(',')
    name='toddy-pam-probe';uid=12345
    assert not any(row.split(':')[0]==name or row.split(':')[2]==str(uid) for row in Path('/etc/passwd').read_text().splitlines())
    subprocess.run(['useradd','-M','-U','-u',str(uid),'-s','/bin/false',name],capture_output=True,check=True)
    password=secrets.token_urlsafe(32)
    result=subprocess.run(['chpasswd','-c','YESCRYPT'],input=name+':'+password+'\n',text=True,capture_output=True,timeout=20)
    assert result.returncode==0,'Ephemeral password creation failed; no output retained'
    shadow=next(row.split(':') for row in Path('/etc/shadow').read_text().splitlines() if row.startswith(name+':'))
    assert shadow[1].startswith('$y$'),'Expected selected yescrypt hash; no hash retained'
    del shadow
    policy=Path('/run/toddy-pam-policy');policy.mkdir(mode=0o755)
    (policy/'toddy-password').write_text('auth required '+str(stage/'usr/lib/security/pam_unix.so')+' nodelay\naccount required '+str(stage/'usr/lib/security/pam_unix.so')+'\n')
    env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','LD_LIBRARY_PATH':str(stage/'usr/lib')}
    runs=[]
    def nnp():
        libc=ctypes.CDLL(None,use_errno=True)
        if libc.prctl(38,1,0,0,0)!=0:raise OSError(ctypes.get_errno(),'child NNP failed')
    def attempt(label,secret,success,username=name,no_new_privileges=False):
        r=subprocess.run([str(fixture/'password-consumer'),str(policy),username],input=secret+'\n',capture_output=True,text=True,timeout=20,env=env,user=uid,group=uid,extra_groups=[],preexec_fn=nnp if no_new_privileges else None)
        assert r.returncode==0,'Password client execution failed: '+label
        row=json.loads(r.stdout);assert row['start']==row['end']==0
        if success:assert row['auth']==row['account']==row['credential']==0,'Expected authentication success: '+label
        else:assert row['auth']!=0,'Expected authentication refusal: '+label
        runs.append({'name':label,'exit':0,'pam_result':row,'uid':uid,'no_new_privileges':no_new_privileges,'expected_authenticated':success})
    attempt('correct-yescrypt-via-setuid-helper',password,True)
    attempt('incorrect-password-refused',secrets.token_urlsafe(32),False)
    attempt('empty-password-refused','',False)
    attempt('unknown-user-refused',password,False,username='toddy-absent-user')
    attempt('helper-no-new-privileges-refused',password,False,no_new_privileges=True)
    subprocess.run(['usermod','-L',name],capture_output=True,check=True)
    attempt('locked-account-refused',password,False)
    subprocess.run(['usermod','-U',name],capture_output=True,check=True)
    attempt('unlock-and-authentication-recovery',password,True)
    password=None
    subprocess.run(['userdel',name],capture_output=True,check=True)
    assert not any(row.startswith(name+':') for row in Path('/etc/passwd').read_text().splitlines())
    assert not any(row.startswith(name+':') for row in Path('/etc/shadow').read_text().splitlines())
    for name,sha in accepted['artifacts'].items():assert digest(fixture/name)==sha
    raw=json.dumps({'scope':'Real native Linux-PAM1.7.2 shadow/yescrypt and setuid helper in disposable overlay only; no installed PAM/login/GDM/GNOME acceptance','kernel':os.uname().release,'pid1':'systemd','fixture_manifest_sha256':digest(fixture/'accepted.json'),'unchanged_fixture_files':len(accepted['artifacts']),'helper':accepted['privileged_helper'],'runs':runs,'ephemeral_account_removed':True,'secrets_retained':False},sort_keys=True).encode()
    encoded=base64.b64encode(zlib.compress(raw,9)).decode();chunks=[encoded[i:i+1024] for i in range(0,len(encoded),1024)]
    for i,chunk in enumerate(chunks):print('TODDY_B02_RUNTIME_DATA',i,chunk,flush=True)
    print('TODDY_B02_RUNTIME_RESULT',json.dumps({'kernel':os.uname().release,'all_selected_exits_zero':True,'report_sha256':hashlib.sha256(raw).hexdigest(),'chunks':len(chunks)}),flush=True)

if __name__=='__main__':
    try:main()
    except Exception as error:
        print('TODDY_B02_RUNTIME_FAIL',type(error).__name__,str(error),flush=True)
        raise

"""Read-only disposable native authentication observer; never enters credentials."""


def auth_facts(expected,round_number,recovery):
    import os,pwd,subprocess,termios,time
    from pathlib import Path
    def run(argv):return subprocess.check_output(argv,text=True,timeout=5).strip()
    assert os.geteuid()==0 and os.uname().release=='7.1.8-toddy'
    root_uuid=run(['/usr/bin/findmnt','-rn','-o','UUID','--mountpoint','/']);assert root_uuid==expected['root_uuid']
    result={'version':1,'round':round_number,'recovery':recovery,'root_uuid':root_uuid,
        'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
        'owner_uid':expected['expected_owner']['uid'],'state':'not-authentication-wait',
        'owner_active':False,'greeter':None,'pam_worker_pid':None,'tty':None}
    sessions=[]
    for line in run(['/usr/bin/loginctl','list-sessions','--no-legend','--no-pager']).splitlines():
        sid=line.split()[0]
        values=dict(row.split('=',1) for row in run(['/usr/bin/loginctl','show-session',sid,'-p','User','-p','Name','-p','Active','-p','Remote','-p','Type','-p','Class','-p','Service']).splitlines())
        sessions.append((sid,values))
        if values.get('User')==str(result['owner_uid']) and values.get('Active')=='yes' and values.get('Class')=='user':result['owner_active']=True
    if result['owner_active']:result['state']='owner-session-active';return result
    if recovery:
        if 'systemd.unit=multi-user.target' not in Path('/proc/cmdline').read_text().split() or Path('/sys/class/tty/tty0/active').read_text().strip()!='tty2':return result
        fd=os.open('/dev/tty2',os.O_RDONLY|os.O_NOCTTY|os.O_NONBLOCK)
        try:
            echo=bool(termios.tcgetattr(fd)[3]&termios.ECHO);foreground=os.tcgetpgrp(fd)
            for row in run(['/usr/bin/ps','-t','tty2','-o','pid=,comm=']).splitlines():
                pid=int(row.split()[0])
                try:
                    if Path('/proc/'+str(pid)+'/exe').resolve()==Path('/usr/bin/login') and os.getpgid(pid)==foreground and not echo:
                        result['tty']={'name':'tty2','echo':False,'foreground_login_pid':pid};result['state']='authentication-wait';break
                except FileNotFoundError:continue
        finally:os.close(fd)
    else:
        gdm=pwd.getpwnam('gdm').pw_uid
        for sid,row in sessions:
            if row=={'User':str(gdm),'Name':'gdm','Active':'yes','Remote':'no','Type':'wayland','Class':'greeter','Service':'gdm-launch-environment'}:result['greeter']={'session':sid,**row}
        if result['greeter'] is None:return result
        for proc in Path('/proc').iterdir():
            if not proc.name.isdigit():continue
            try:
                if (proc/'exe').resolve()!=Path('/usr/libexec/gdm-session-worker') or proc.stat().st_uid!=0:continue
                arguments=(proc/'cmdline').read_bytes().split(b'\0')
                if any(b'pam/gdm-password' in arg for arg in arguments):result['pam_worker_pid']=int(proc.name);result['state']='authentication-wait';break
            except (FileNotFoundError,PermissionError):continue
    return result


def start_auth_wait(expected,round_number,recovery):
    import json,threading,time,termios
    def observer():
        deadline=time.monotonic()+840;sequence=0
        with open('/dev/ttyS1','w',buffering=1) as stream:
            while time.monotonic()<deadline:
                sequence+=1
                try:result=auth_facts(expected,round_number,recovery)
                except Exception:result={'version':1,'round':round_number,'state':'authentication-observation-unavailable','owner_active':None}
                result['sequence']=sequence
                stream.write('TODDY_INSTALLED_AUTH '+json.dumps(result,sort_keys=True)+'\n');stream.flush();termios.tcdrain(stream.fileno())
                if result.get('owner_active') is True:return
                time.sleep(.25)
    threading.Thread(target=observer,name='native-auth-observer',daemon=True).start()

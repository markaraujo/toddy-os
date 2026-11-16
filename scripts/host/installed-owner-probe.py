#!/usr/bin/env python3
"""Qualification observer with explicit owner file and one clock preference probe.

Supplied as a public read-only firmware credential, never installed in the OS.
No login injection, passwords, autologin change, task engine or network activity.
"""
import hashlib,json,os,pwd,re,stat,subprocess,termios,time
from pathlib import Path
try:run_owner_state
except NameError:
    import sys
    sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
    from scripts.build.phase2.owner_setting_evidence import run_owner_state,owner_marker


def command(argv):
    return subprocess.check_output(argv,text=True,timeout=15).strip()


def observe(expected,round_number,recovery=False):
    assert os.geteuid()==0 and round_number in (1,2,3)
    owner=expected['expected_owner'];account=pwd.getpwnam(owner['username'])
    assert (account.pw_uid,account.pw_gid)==(owner['uid'],owner['gid'])
    assert account.pw_dir=='/home/'+owner['username']
    assert os.uname().release=='7.1.8-toddy'
    root=json.loads(command(['/usr/bin/findmnt','--json','--target','/','--output','TARGET,SOURCE,FSTYPE,UUID']))['filesystems']
    assert len(root)==1 and root[0]['target']=='/' and root[0]['fstype']=='ext4' and root[0]['uuid']==expected['root_uuid']
    disks=json.loads(command(['/usr/bin/lsblk','--json','--nodeps','--output','TYPE,SERIAL']))['blockdevices']
    assert len(disks)==1 and disks[0]['type']=='disk' and disks[0]['serial']==expected['target_serial']
    sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
    assert sha('/boot/vmlinuz-7.1.8-toddy')==expected['kernel_sha256']
    assert sha('/boot/initramfs-7.1.8-toddy-installed.img')==expected['initramfs_sha256']
    assert sha('/etc/toddy/grub.cfg')==expected['grub_config_sha256']
    mode='tty' if recovery else 'wayland';session=None
    deadline=time.monotonic()+840
    while time.monotonic()<deadline:
        for line in command(['/usr/bin/loginctl','list-sessions','--no-legend','--no-pager']).splitlines():
            sid=line.split()[0]
            values=dict(row.split('=',1) for row in command(['/usr/bin/loginctl','show-session',sid,
                '-p','User','-p','Name','-p','Active','-p','Remote','-p','Type','-p','Class','-p','Service']).splitlines())
            if (values.get('User')==str(owner['uid']) and values.get('Name')==owner['username'] and
                    values.get('Active')=='yes' and values.get('Remote')=='no' and values.get('Type')==mode and
                    values.get('Class')=='user' and values.get('Service')==('login' if recovery else 'gdm-password')):
                session=sid;break
        if session:break
        time.sleep(1)
    assert session,'actual fresh owner login not observed'
    if recovery:
        assert 'systemd.unit=multi-user.target' in Path('/proc/cmdline').read_text().split()
        assert command(['/usr/bin/systemctl','is-active','multi-user.target'])=='active'
        gdm=subprocess.run(['/usr/bin/systemctl','is-active','gdm.service'],capture_output=True,text=True,timeout=15)
        assert gdm.returncode!=0
    else:
        assert 'systemd.unit=multi-user.target' not in Path('/proc/cmdline').read_text().split()
        assert command(['/usr/bin/systemctl','is-active','gdm.service'])=='active'
        # An actual GNOME shell must belong to the authenticated owner session.
        assert subprocess.run(['/usr/bin/pgrep','-u',str(owner['uid']),'-x','gnome-shell'],stdout=subprocess.DEVNULL,timeout=15).returncode==0
    measured=run_owner_state(account,{'operation_id':expected['operation_id'],'plan_sha256':expected['plan_sha256']},round_number,recovery)
    assert measured['marker_sha256']==hashlib.sha256(owner_marker(expected['plan_sha256'])).hexdigest(),'owner file and setting persistence failed'
    bootid=Path('/proc/sys/kernel/random/boot_id').read_text().strip();assert re.fullmatch('[0-9a-f-]{36}',bootid)
    return {'boot_id':bootid,'root_uuid':root[0]['uuid'],'persistent_marker_sha256':measured['marker_sha256'],'owner_setting':measured['setting'],
        'kernel_release':os.uname().release,'installer_media_attached':False,'fresh_owner_login':True,
        'initramfs_sha256':expected['initramfs_sha256'],'session_type':mode,'round':round_number,
        'recovery':recovery,'observer_only_extra_write':'explicit-owner-file-marker-and-clock-preference'}


def main():
    # EXPECTED/ROUND/RECOVERY are literal public values prefixed by the controller.
    try:report={'state':'observed','observation':observe(EXPECTED,ROUND,RECOVERY)}
    except BaseException as error:report={'state':'failed','error':type(error).__name__}
    with open('/dev/ttyS1','w',buffering=1) as stream:
        stream.write('TODDY_INSTALLED_OWNER '+json.dumps(report,sort_keys=True)+'\n');stream.flush();termios.tcdrain(stream.fileno())
    assert report['state']=='observed','real installed owner observation failed'

if __name__=='__main__':main()

"""Actual installed GDM on a virtual DRM/input seat; no authentication bypass."""
from pathlib import Path
import base64
import hashlib
import json
import os
import re
import select
import resource
import subprocess
import termios
import time
import zlib


def command(args, timeout=25):
    r = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    return {'args': args, 'exit': r.returncode, 'stdout': r.stdout, 'stderr': r.stderr}


def main():
    assert os.geteuid() == 0 and os.uname().release == '7.1.8-toddy'
    assert Path('/proc/1/comm').read_text().strip() == 'systemd'
    device = command(['findmnt', '-n', '-o', 'SOURCE', '/'])['stdout'].strip()
    assert re.fullmatch('/dev/[a-z0-9]+', device)
    parent = command(['lsblk', '-ndo', 'PKNAME', device])['stdout'].strip()
    assert command(['lsblk', '-dnro', 'SERIAL', '/dev/'+parent])['stdout'].strip() == 'TODDY-BOOT-TEST'
    assert command(['dpkg-query', '-W', '-f=${Version}', 'gtk'])['stdout'] == '4.22.4-1+toddy13'
    cache = Path('/usr/share/glib-2.0/schemas/gschemas.compiled')
    digest = hashlib.sha256(cache.read_bytes()).hexdigest()
    assert digest == 'a352c74e50964dca946948f2e80e9345a175615c938c65295f1bb44623133e1b'
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    fd = os.open('/dev/ttyS2',os.O_RDWR|os.O_NOCTTY)
    attrs = termios.tcgetattr(fd)
    attrs[0] = attrs[1] = attrs[3] = 0
    attrs[2] |= termios.CLOCAL|termios.CREAD
    attrs[4] = attrs[5] = termios.B115200
    termios.tcsetattr(fd,termios.TCSANOW,attrs)
    transport = os.fdopen(fd,'r+b',buffering=0)
    transport.write(b'READY\n')
    assert select.select([transport],[],[],90)[0], 'Private fixture channel missing'
    credential = transport.readline(64).strip()
    assert re.fullmatch(b'[a-z]{24}',credential), 'Invalid private fixture transport'
    username = 'toddy-preview'
    assert not Path('/home',username).exists()
    subprocess.run(['useradd','-m','-U','-u','12402','-c','Toddy Preview','-s','/bin/bash',username],check=True,capture_output=True,timeout=20)
    changed = subprocess.run(['chpasswd','-c','SHA512'],input=username.encode()+b':'+credential+b'\n',capture_output=True,timeout=20)
    credential = None
    assert changed.returncode==0, 'Private disposable account configuration failed'
    transport.write(b'CONFIGURED\n')
    home=Path('/home',username)
    documents=home/'Documents';documents.mkdir(exist_ok=True)
    for name in ['toddy-restore']:
        p=documents/name;p.write_text('toddy-files-native\n');os.chown(p,12402,12402)
    os.chown(documents,12402,12402)
    assert command(['dpkg-query','-W','-f=${Version}','nautilus'])['stdout']=='50.2.2-1+toddy1'
    transitions={'observed_trashed':False,'observed_restored_after_trash':False}
    seed=documents/'toddy-restore';trash=home/'.local/share/Trash/files/toddy-restore'
    def observe_transition():
        try:
            if not seed.exists() and trash.is_file() and trash.read_text()=='toddy-files-native\n':transitions['observed_trashed']=True
            if transitions['observed_trashed'] and seed.is_file() and seed.read_text()=='toddy-files-native\n' and not trash.exists():transitions['observed_restored_after_trash']=True
        except FileNotFoundError:pass
    report = {'scope': 'Affected installed Files Trash navigation/restoration/recovery and noninteractive active-client authorization challenge. Seed file explicitly fixture-created before app launch. Synthetic credential only in memory/private transient channel. No autologin or session-policy bypass; actual GUI navigation/input/screenshots require separate visual review; no B02/physical completion.',
              'kernel': os.uname().release, 'schema_sha256': digest,
              'all_selected_exits_zero': False, 'runs': []}
    try:
        for args in [['systemctl','start','dbus.service','systemd-logind.service','systemd-userdbd.service'],
                     ['udevadm','settle','--timeout=20'], ['systemctl','start','gdm.service']]:
            report['runs'].append(command(args, timeout=45))
        deadline = time.monotonic() + 600
        owner = None
        requested_finish = False
        while time.monotonic() < deadline:
            observe_transition()
            sessions = command(['loginctl','list-sessions','--no-legend','--no-pager'])
            for line in sessions['stdout'].splitlines():
                session = line.split()[0]
                r = command(['loginctl','show-session',session,'-p','Class','-p','Type','-p','State','-p','Seat','-p','Name'])
                properties = dict(s.split('=',1) for s in r['stdout'].splitlines() if '=' in s)
                if properties.get('Class') == 'user' and properties.get('Name') == username and properties.get('Seat') == 'seat0' and properties.get('Type') == 'wayland' and properties.get('State') == 'active':
                    owner = {'session_id':session, 'properties':properties}
            if select.select([transport],[],[],1)[0]:
                requested_finish = transport.readline(64)==b'DONE\n'
                break
            if command(['systemctl','is-failed','gdm.service'])['stdout'].strip() == 'failed':
                break
        observe_transition()
        report['file_postconditions']={**transitions,
            'restored_seed_exact':seed.is_file() and seed.read_text()=='toddy-files-native\n',
            'trash_entry_absent_after_restore':not trash.exists()}
        environment=['HOME='+str(home),'XDG_RUNTIME_DIR=/run/user/12402','DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/12402/bus','LC_ALL=C.UTF-8']
        report['installed_trash_info']=command(['runuser','-u',username,'--','env',*environment,'gio','info','trash:///'])
        pids=command(['pgrep','-u','12402','-x','nautilus'])
        active=[int(p) for p in pids['stdout'].split()]
        assert len(active)==1,'Expected actual installed Files client'
        client=active[0];assert Path('/proc',str(client)).stat().st_uid==12402
        start=Path('/proc',str(client),'stat').read_text().split()[21]
        report['unprivileged_client_authorization']=command(['runuser','-u',username,'--','pkcheck','--action-id','org.gtk.vfs.file-operations','--process',f'{client},{start},12402'])
        report['owner_session'] = owner
        report['host_requested_finish'] = requested_finish
        for args in [['systemctl','status','gdm.service','--no-pager','-l'],
                     ['loginctl','seat-status','seat0','--no-pager'],
                     ['loginctl','list-sessions','--no-pager'],
                     ['ps','-eo','pid,uid,tty,args'],
                     ['journalctl','-b','-u','gdm.service','--no-pager','-n','150'],
                     ['journalctl','-b','--no-pager','-n','250']]:
            report['runs'].append(command(args))
        report['devices'] = {'drm': sorted(p.name for p in Path('/sys/class/drm').glob('*')),
                             'input': Path('/proc/bus/input/devices').read_text()}
        report['all_selected_exits_zero'] = owner is not None and requested_finish and all(report['file_postconditions'].values()) and report['installed_trash_info']['exit']==0 and report['unprivileged_client_authorization']['exit']==2 and all(r['exit']==0 for r in report['runs'][:3])
    except Exception as error:
        report['error'] = {'type':type(error).__name__, 'message':str(error)}
    finally:
        transport.close()
        report['gdm_stop'] = command(['systemctl','stop','gdm.service'], timeout=40)
        report['schema_unchanged'] = hashlib.sha256(cache.read_bytes()).hexdigest() == digest
        report['all_selected_exits_zero'] &= report['gdm_stop']['exit']==0 and report['schema_unchanged']
    raw = json.dumps(report, sort_keys=True).encode()
    assert len(raw) < 4*1024**2
    encoded = base64.b64encode(zlib.compress(raw,9)).decode()
    chunks = [encoded[i:i+1024] for i in range(0,len(encoded),1024)]
    fd = os.open('/dev/ttyS1',os.O_WRONLY|os.O_NOCTTY)
    attrs = termios.tcgetattr(fd)
    attrs[0] = attrs[1] = attrs[3] = 0
    attrs[2] |= termios.CLOCAL|termios.CREAD
    attrs[4] = attrs[5] = termios.B115200
    termios.tcsetattr(fd,termios.TCSANOW,attrs)
    with os.fdopen(fd,'w',buffering=1) as evidence:
        for i,chunk in enumerate(chunks):
            print('TODDY_B02_RUNTIME_DATA',i,chunk,file=evidence,flush=True)
        print('TODDY_B02_RUNTIME_RESULT',json.dumps({'kernel':os.uname().release,'all_selected_exits_zero':report['all_selected_exits_zero'],'report_sha256':hashlib.sha256(raw).hexdigest(),'chunks':len(chunks)}),file=evidence,flush=True)
        termios.tcdrain(evidence.fileno())
    if not report['all_selected_exits_zero']:
        raise AssertionError('Normal GDM seat gate failed; preserve report and scanout')


if __name__ == '__main__':
    main()

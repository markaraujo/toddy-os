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
    assert command(['dpkg-query', '-W', '-f=${Version}', 'gtk'])['stdout'] == '4.22.4-1+toddy14'
    cache = Path('/usr/share/glib-2.0/schemas/gschemas.compiled')
    digest = hashlib.sha256(cache.read_bytes()).hexdigest()
    assert digest == '5bc2947ffc5874cc735c33c2611bd6aa960061d7e6c992519efe984ea52d89e1'
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
    def user_command(args,timeout=25):
        environment={'HOME':str(home),'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8',
            'XDG_RUNTIME_DIR':'/run/user/12402','DBUS_SESSION_BUS_ADDRESS':'unix:path=/run/user/12402/bus','WAYLAND_DISPLAY':'wayland-0'}
        p=subprocess.run(args,user=12402,group=12402,extra_groups=[],cwd=home,env=environment,
                         capture_output=True,text=True,timeout=timeout)
        return {'args':args,'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
    import gzip,traceback
    assert hashlib.sha256(gzip.decompress(Path('/proc/config.gz').read_bytes())).hexdigest()=='952e7d9d6e5c8e523ebf128c220481bc29280424e0686e4b0903b518234bf77b'
    report={'scope':'Final selected native Tecla keyboard viewer/focus/narrow window/close and Git in ordinary navy Terminal. Prior approved browser/files/editor/network/audio/portal proofs reused; no whole Phase2/physical/ISO acceptance.','all_selected_exits_zero':False,'schema_sha256':digest}
    owner=None;finished=False;phases=[]
    def processes(exe):
        rows=[]
        for p in Path('/proc').glob('[0-9]*'):
            try:
                if (p/'exe').readlink()==Path(exe):
                    props=dict(l.split(':',1) for l in (p/'status').read_text().splitlines() if ':' in l)
                    if props['Uid'].split()[0]=='12402':rows.append({'pid':int(p.name),'uid':12402,'CapEff':props['CapEff'].strip(),'NoNewPrivs':props['NoNewPrivs'].strip()})
            except (OSError,KeyError):pass
        return rows
    try:
        deadline=time.monotonic()+660
        while time.monotonic()<deadline:
            if not owner:
                for line in command(['loginctl','list-sessions','--no-legend','--no-pager'])['stdout'].splitlines():
                    sid=line.split()[0];r=command(['loginctl','show-session',sid,'-p','Class','-p','Type','-p','State','-p','Seat','-p','Name']);props=dict(l.split('=',1) for l in r['stdout'].splitlines() if '=' in l)
                    if props=={'Class':'user','Name':username,'Type':'wayland','State':'active','Seat':'seat0'}:owner={'session_id':sid,'properties':props}
                if owner:
                    until=time.monotonic()+30
                    while time.monotonic()<until and not Path('/run/user/12402/wayland-0').exists():time.sleep(.2)
                    assert Path('/run/user/12402/wayland-0').exists()
                    report['package_versions']={n:command(['dpkg-query','-W','-f=${Version}',n])['stdout'] for n in ['git','tecla','gnome-terminal','gtk']}
                    assert report['package_versions']['git']=='2.55.0-1+toddy1' and report['package_versions']['tecla']=='50.0-1+toddy1'
                    print('TODDY_DESKTOP_FINAL_UI_READY',flush=True)
            if select.select([transport],[],[],1)[0]:
                row=transport.readline(128).strip().decode()
                if row=='DONE':finished=True;break
                assert row.startswith('PHASE ');phase=row[6:];assert owner and phase not in phases;phases.append(phase)
                if phase=='keyboard-verified':
                    rows=processes('/usr/bin/tecla');assert len(rows)==1 and int(rows[0]['CapEff'],16)==0
                    report['actual_tecla_process']=rows[0]
                    report['input_sources']=user_command(['gsettings','get','org.gnome.desktop.input-sources','sources'])
                elif phase=='keyboard-closed':
                    until=time.monotonic()+10
                    while time.monotonic()<until and processes('/usr/bin/tecla'):time.sleep(.2)
                    assert not processes('/usr/bin/tecla');report['tecla_closed']=True
                elif phase=='git-terminal-verified':
                    repo=home/'git-terminal-proof';assert repo.is_dir() and repo.stat().st_uid==12402 and (repo/'.git/config').is_file()
                    check=user_command(['git','-C',str(repo),'rev-parse','--is-inside-work-tree']);assert check['exit']==0 and check['stdout'].strip()=='true';report['terminal_created_git_repository']=check
                    terminals=processes('/usr/libexec/gnome-terminal-server');assert len(terminals)==1 and int(terminals[0]['CapEff'],16)==0;report['actual_terminal_process']=terminals[0]
                else:raise AssertionError('Unexpected selected phase '+phase)
        assert owner and finished and {'keyboard-verified','keyboard-closed','git-terminal-verified'}<=set(phases)
        report.update(owner_session=owner,ui_phase_annotations=phases,all_selected_exits_zero=True)
    except Exception as error:report.update(error={'type':type(error).__name__,'message':str(error)},traceback=traceback.format_exc(),ui_phase_annotations=phases,diagnostics=command(['journalctl','-b','--no-pager','-n','100']))
    finally:
        transport.close();report['gdm_stop']=command(['systemctl','stop','gdm.service'],timeout=40);report['all_selected_exits_zero'] &= report['gdm_stop']['exit']==0
    raw=json.dumps(report,sort_keys=True).encode();packed=base64.b64encode(zlib.compress(raw,9)).decode();chunks=[packed[i:i+1024] for i in range(0,len(packed),1024)]
    fd=os.open('/dev/ttyS1',os.O_WRONLY|os.O_NOCTTY);attrs=termios.tcgetattr(fd);attrs[0]=attrs[1]=attrs[3]=0;attrs[2]|=termios.CLOCAL|termios.CREAD;attrs[4]=attrs[5]=termios.B115200;termios.tcsetattr(fd,termios.TCSANOW,attrs)
    with os.fdopen(fd,'w',buffering=1) as out:
        for i,part in enumerate(chunks):print('TODDY_B02_RUNTIME_DATA',i,part,file=out,flush=True)
        print('TODDY_B02_RUNTIME_RESULT',json.dumps({'kernel':os.uname().release,'all_selected_exits_zero':report['all_selected_exits_zero'],'report_sha256':hashlib.sha256(raw).hexdigest(),'chunks':len(chunks)}),file=out,flush=True);termios.tcdrain(out.fileno())
    assert report['all_selected_exits_zero'],'Selected final native desktop UI gate failed'
if __name__=='__main__':main()

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
    def user_command(args,timeout=25):
        environment={'HOME':str(home),'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8',
            'XDG_RUNTIME_DIR':'/run/user/12402','DBUS_SESSION_BUS_ADDRESS':'unix:path=/run/user/12402/bus'}
        p=subprocess.run(args,user=12402,group=12402,extra_groups=[],cwd=home,env=environment,
                         capture_output=True,text=True,timeout=timeout)
        return {'args':args,'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
    report={'scope':'Actual native navy/Terminal/session audio/controls and absent-agent desktop in disposable VM. Virtual audio capture separately required; no physical/whole B02 acceptance.',
            'kernel':os.uname().release,'schema_sha256':digest,'all_selected_exits_zero':False}
    owner=None;finished=False;phases=[];volumes=[];audio_done=False
    try:
        assert command(['systemctl','get-default'])['stdout'].strip()=='graphical.target'
        limit=time.monotonic()+75
        while time.monotonic()<limit:
            graphical=command(['systemctl','is-active','graphical.target']);gdm=command(['systemctl','is-active','gdm.service'])
            if graphical['stdout'].strip()==gdm['stdout'].strip()=='active':break
            time.sleep(1)
        assert graphical['stdout'].strip()==gdm['stdout'].strip()=='active','Normal default boot failed'
        report['default_graphical_boot']={'graphical':graphical,'gdm':gdm}
        deadline=time.monotonic()+660
        while time.monotonic()<deadline:
            if not owner:
                sessions=command(['loginctl','list-sessions','--no-legend','--no-pager'])
                for line in sessions['stdout'].splitlines():
                    sid=line.split()[0];values=command(['loginctl','show-session',sid,'-p','Class','-p','Type','-p','State','-p','Seat','-p','Name'])
                    props=dict(x.split('=',1) for x in values['stdout'].splitlines() if '=' in x)
                    if props=={'Class':'user','Name':username,'Type':'wayland','State':'active','Seat':'seat0'}:owner={'session_id':sid,'properties':props}
            if owner and not audio_done:
                limit=time.monotonic()+25
                units=['pipewire.service','pipewire-pulse.service','wireplumber.service']
                while time.monotonic()<limit:
                    active=user_command(['systemctl','--user','is-active',*units])
                    if active['exit']==0 and active['stdout'].split()==['active']*3:break
                    time.sleep(1)
                report['session_audio_units']=active
                assert active['exit']==0 and active['stdout'].split()==['active']*3,'Session audio did not start automatically'
                report['alsa_cards']=Path('/proc/asound/cards').read_text();assert 'HDA' in report['alsa_cards']
                report['pulse_info']=user_command(['pactl','info']);assert report['pulse_info']['exit']==0 and 'PipeWire' in report['pulse_info']['stdout']
                report['sinks']=user_command(['pactl','list','short','sinks']);assert report['sinks']['exit']==0 and 'alsa_output.' in report['sinks']['stdout']
                import wave,math,struct
                tone=home/'audio-proof.wav'
                with wave.open(str(tone),'wb') as w:
                    w.setnchannels(2);w.setsampwidth(2);w.setframerate(44100)
                    w.writeframes(b''.join(struct.pack('<hh',*( [int(10000*math.sin(2*math.pi*440*i/44100))]*2 )) for i in range(44100*2)))
                os.chown(tone,12402,12402)
                report['tone_playback']=user_command(['paplay',str(tone)],timeout=15);assert report['tone_playback']['exit']==0
                text=home/'terminal-utf8.txt';text.write_text('Toddy OS — Ação, café e português.\n');os.chown(text,12402,12402)
                audio_done=True
            if owner:
                v=user_command(['wpctl','get-volume','@DEFAULT_AUDIO_SINK@'])
                if v['exit']==0 and v['stdout'].strip() not in volumes:volumes.append(v['stdout'].strip())
            if select.select([transport],[],[],.5)[0]:
                message=transport.readline(128).decode().strip()
                if message=='DONE':finished=True;break
                if message.startswith('PHASE '):phases.append(message[6:])
        report.update(owner_session=owner,host_requested_finish=finished,ui_phase_annotations=phases,observed_volumes=volumes)
        assert owner and finished and audio_done
        assert {'terminal-verified','audio-verified','navy-verified'}<=set(phases)
        assert any('[MUTED]' in v for v in volumes) and any('[MUTED]' not in v for v in volumes),'Actual mute/unmute state not observed'
        assert (home/'terminal-proof.txt').read_bytes()==b'Toddy OK\n','Native Terminal command file missing'
        report['terminal_file']={'sha256':hashlib.sha256((home/'terminal-proof.txt').read_bytes()).hexdigest(),'bytes':9}
        settings=user_command(['python3','-c',"from gi.repository import Gio; import json; b=Gio.Settings.new('org.gnome.desktop.background'); i=Gio.Settings.new('org.gnome.desktop.interface'); p=Gio.Settings.new_with_path('org.gnome.Terminal.Legacy.Profile','/org/gnome/terminal/legacy/profiles:/:b1dcc9dd-5262-4d8d-a863-c897e6d979b9/'); print(json.dumps({'background':b.get_string('primary-color'),'scheme':i.get_string('color-scheme'),'terminal_background':p.get_string('background-color'),'terminal_foreground':p.get_string('foreground-color'),'system_font':p.get_boolean('use-system-font')}))"])
        assert settings['exit']==0
        report['settings']=json.loads(settings['stdout'])
        assert report['settings']=={'background':'#081b33','scheme':'prefer-dark','terminal_background':'#081b33','terminal_foreground':'#f4f7fb','system_font':True}
        report['agent_package_absent']=command(['dpkg-query','-W','toddy-agent']);assert report['agent_package_absent']['exit']!=0
        report['boot_timing']=command(['systemd-analyze','time'])
        report['memory_snapshot']=Path('/proc/meminfo').read_text()
        report['all_selected_exits_zero']=True
    except Exception as error:
        report.update(owner_session=owner,host_requested_finish=finished,ui_phase_annotations=phases,observed_volumes=volumes,error={'type':type(error).__name__,'message':str(error)})
        report['diagnostics']=[command(a) for a in [['systemctl','status','gdm.service','graphical.target','--no-pager','-l'],['journalctl','-b','--no-pager','-n','100']]]
        if owner:report['user_diagnostics']=user_command(['journalctl','--user','-b','--no-pager','-n','100'])
    finally:
        transport.close();report['gdm_stop']=command(['systemctl','stop','gdm.service'],timeout=40)
        report['schema_unchanged']=hashlib.sha256(cache.read_bytes()).hexdigest()==digest
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
        raise AssertionError('Native desktop integration gate failed; preserve report and scanout')


if __name__ == '__main__':
    main()

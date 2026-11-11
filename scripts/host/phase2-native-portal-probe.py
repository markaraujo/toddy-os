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
    report={'scope':'Actual installed-kernel FUSE helper and native GNOME portal settings/file chooser/Close in disposable VM. Virtual seat only; no physical/whole B02 acceptance.','kernel':os.uname().release,'schema_sha256':digest,'all_selected_exits_zero':False}
    owner=None;finished=False;phases=[];clients={};settings=[];fuse=None
    def user_spawn(args,label):
        logfile=home/('portal-'+label+'.log');output=logfile.open('x')
        p=subprocess.Popen(args,user=12402,group=12402,extra_groups=[],cwd=home,env={'HOME':str(home),'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','XDG_RUNTIME_DIR':'/run/user/12402','DBUS_SESSION_BUS_ADDRESS':'unix:path=/run/user/12402/bus','WAYLAND_DISPLAY':'wayland-0'},stdin=subprocess.DEVNULL,stdout=output,stderr=subprocess.STDOUT)
        return p,output,logfile
    def portal_value():
        result=user_command(['python3','-c',"import gi,json;from gi.repository import Gio,GLib;b=Gio.bus_get_sync(Gio.BusType.SESSION,None);v=b.call_sync('org.freedesktop.portal.Desktop','/org/freedesktop/portal/desktop','org.freedesktop.portal.Settings','Read',GLib.Variant('(ss)',('org.freedesktop.appearance','color-scheme')),None,Gio.DBusCallFlags.NONE,30000,None).unpack()[0];\nwhile isinstance(v,GLib.Variant):v=v.unpack()\nprint(json.dumps(v))"],timeout=40)
        assert result['exit']==0,result
        return json.loads(result['stdout'])
    def finish_client(mode):
        p,output,logfile=clients[mode];code=p.wait(timeout=15);output.flush();assert code==0,(mode,logfile.read_text())
        rows=[json.loads(l) for l in logfile.read_text().splitlines() if l.startswith('{')];assert rows[-1]['state']=='complete'
        report.setdefault('filechooser',{})[mode]=rows[-1]
    try:
        assert command(['systemctl','get-default'])['stdout'].strip()=='graphical.target'
        deadline=time.monotonic()+720
        while time.monotonic()<deadline:
            if not owner:
                sessions=command(['loginctl','list-sessions','--no-legend','--no-pager'])
                for line in sessions['stdout'].splitlines():
                    sid=line.split()[0];values=command(['loginctl','show-session',sid,'-p','Class','-p','Type','-p','State','-p','Seat','-p','Name'])
                    props=dict(x.split('=',1) for x in values['stdout'].splitlines() if '=' in x)
                    if props=={'Class':'user','Name':username,'Type':'wayland','State':'active','Seat':'seat0'}:owner={'session_id':sid,'properties':props}
                if owner:
                    ready_deadline=time.monotonic()+30
                    while time.monotonic()<ready_deadline:
                        if (Path('/run/user/12402')/'wayland-0').exists():break
                        time.sleep(.2)
                    assert (Path('/run/user/12402')/'wayland-0').exists(),'Compositor Wayland socket did not become ready after normal login'
                    report['fuse']=verify_native_fuse(previous=FUSE_PREVIOUS);assert report['fuse']['all_selected_exits_zero'],report['fuse']
                    source=home/'portal-client.py';source.write_text(PORTAL_CLIENT_SOURCE);os.chown(source,12402,12402);source.chmod(0o644)
                    allowed=home/'portal-allowed.txt';allowed.write_text('Toddy native portal consent\n');os.chown(allowed,12402,12402)
                    value=portal_value();assert value==1,value;settings.append({'state':'default-dark','portal_color_scheme':value})
                    report['initial_user_portal_services']=user_command(['systemctl','--user','is-active','xdg-desktop-portal.service','xdg-desktop-portal-gnome.service'])
                    assert report['initial_user_portal_services']['exit']==0
                    report['ready_for_native_ui']=True
                    print('TODDY_PORTAL_UI_READY',flush=True)
            if select.select([transport],[],[],1)[0]:
                row=transport.readline(128).strip().decode()
                if row=='DONE':finished=True;break
                assert row.startswith('PHASE '),row
                phase=row[6:];assert phase not in phases,phase;phases.append(phase)
                assert owner,'Normal GDM/PAM owner session required'
                if phase in ['portal-light','portal-dark']:
                    expected=0 if phase=='portal-light' else 1;value=portal_value();assert value==expected,(phase,value)
                    settings.append({'state':phase,'portal_color_scheme':value})
                elif phase=='portal-chooser-allow':
                    assert 'portal-light' in phases and 'portal-dark' in phases
                    clients['allow']=user_spawn(['python3',str(home/'portal-client.py'),'allow',str(home/'portal-allow-marker')],'allow')
                elif phase=='portal-chooser-cancel':
                    finish_client('allow');clients['cancel']=user_spawn(['python3',str(home/'portal-client.py'),'cancel',str(home/'portal-cancel-marker')],'cancel')
                elif phase=='portal-chooser-close':
                    finish_client('cancel');clients['close']=user_spawn(['python3',str(home/'portal-client.py'),'close',str(home/'portal-close-marker')],'close')
                elif phase=='portal-close-now':
                    marker=home/'portal-close-marker';assert not marker.exists();marker.write_text('close-request\n');os.chown(marker,12402,12402)
                elif phase=='portal-complete':finish_client('close')
                else:raise AssertionError('Unexpected native portal UI phase '+phase)
        assert owner and finished and {'portal-light','portal-dark','portal-chooser-allow','portal-chooser-cancel','portal-chooser-close','portal-close-now','portal-complete'}<=set(phases)
        report.update(owner_session=owner,ui_phase_annotations=phases,portal_settings=settings)
        report['agent_package_absent']=command(['dpkg-query','-W','toddy-agent']);assert report['agent_package_absent']['exit']!=0
        report['boot_timing']=command(['systemd-analyze','time'])
        report['all_selected_exits_zero']=True
    except Exception as error:
        import traceback
        report['traceback']=traceback.format_exc()
        report.update(owner_session=owner,host_requested_finish=finished,ui_phase_annotations=phases,portal_settings=settings,error={'type':type(error).__name__,'message':str(error)})
        report['diagnostics']=[command(a) for a in [['systemctl','status','gdm.service','graphical.target','--no-pager','-l'],['journalctl','-b','--no-pager','-n','100']]]
        if owner:report['user_diagnostics']=user_command(['journalctl','--user','-b','--no-pager','-n','150'])
    finally:
        for mode,(p,output,logfile) in clients.items():
            if p.poll() is None:p.terminate();p.wait(timeout=15)
            output.close();report.setdefault('client_logs',{})[mode]=logfile.read_text()
        transport.close();report['gdm_stop']=command(['systemctl','stop','gdm.service'],timeout=40)
        report['schema_unchanged']=hashlib.sha256(cache.read_bytes()).hexdigest()==digest
        report['all_selected_exits_zero'] &= report['gdm_stop']['exit']==0 and report['schema_unchanged']
    raw=json.dumps(report,sort_keys=True).encode();assert len(raw)<4*1024**2
    encoded=base64.b64encode(zlib.compress(raw,9)).decode();chunks=[encoded[i:i+1024] for i in range(0,len(encoded),1024)]
    fd=os.open('/dev/ttyS1',os.O_WRONLY|os.O_NOCTTY);attrs=termios.tcgetattr(fd);attrs[0]=attrs[1]=attrs[3]=0;attrs[2]|=termios.CLOCAL|termios.CREAD;attrs[4]=attrs[5]=termios.B115200;termios.tcsetattr(fd,termios.TCSANOW,attrs)
    with os.fdopen(fd,'w',buffering=1) as evidence:
        for i,chunk in enumerate(chunks):print('TODDY_B02_RUNTIME_DATA',i,chunk,file=evidence,flush=True)
        print('TODDY_B02_RUNTIME_RESULT',json.dumps({'kernel':os.uname().release,'all_selected_exits_zero':report['all_selected_exits_zero'],'report_sha256':hashlib.sha256(raw).hexdigest(),'chunks':len(chunks)}),file=evidence,flush=True);termios.tcdrain(evidence.fileno())
    if not report['all_selected_exits_zero']:raise AssertionError('Native FUSE/portal gate failed; preserve report/scanout')

if __name__=='__main__':main()

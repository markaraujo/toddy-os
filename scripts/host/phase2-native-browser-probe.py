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

FIXTURES = None


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
    fixture=home/'browser-fixture';fixture.mkdir();os.chown(fixture,12402,12402)
    assert FIXTURES and set(FIXTURES)=={'index.html','second.html'}
    for name,text in FIXTURES.items():
        p=fixture/name;p.write_text(text);os.chown(p,12402,12402);p.chmod(0o444)
    server_script=home/'browser-http-server.py'
    server_script.write_text("""from pathlib import Path
import http.server,json,select,socket,threading,time
LOG=Path.home()/'browser-http-events.jsonl'
LOCK=threading.Lock()
def record(event):
 with LOCK:
  with LOG.open('a') as f:f.write(json.dumps(event)+'\\n')
class Handler(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
 def do_GET(self):
  record({'event':'get','path':self.path})
  if self.path.split('?')[0]!='/slow':return super().do_GET()
  record({'event':'slow-started'})
  end=time.monotonic()+90
  while time.monotonic()<end:
   if select.select([self.connection],[],[],.2)[0]:
    try:data=self.connection.recv(1,socket.MSG_PEEK)
    except OSError:record({'event':'slow-cancelled'});return
    if not data:record({'event':'slow-cancelled'});return
  record({'event':'slow-deadline-not-success'})
  self.send_error(408)
http.server.ThreadingHTTPServer(('127.0.0.1',8765),Handler).serve_forever()
""")
    os.chown(server_script,12402,12402);server_script.chmod(0o444)
    report={'scope':'Actual default graphical boot/normal GDM owner and installed browser process, restart and content sandbox. Native UI phase annotations require retained scanouts; no physical/whole B02 acceptance.',
            'kernel':os.uname().release,'schema_sha256':digest,'all_selected_exits_zero':False}
    server=None;owner=None;finished=False;phases=[];seen=[];stopped=False;reopened=False;network_off=False
    def processes():
        main=[];content=[]
        for p in Path('/proc').iterdir():
            if not p.name.isdigit():continue
            try:
                if p.stat().st_uid!=12402:continue
                exe=(p/'exe').resolve()
                if exe not in [Path('/usr/lib/firefox/firefox'),Path('/usr/lib/firefox/firefox-bin')]:continue
                args=(p/'cmdline').read_bytes().split(b'\0');name=(p/'comm').read_text().strip()
                status=dict(line.split(':',1) for line in (p/'status').read_text().splitlines() if ':' in line)
                row={'pid':int(p.name),'start_ticks':(p/'stat').read_text().rsplit(')',1)[1].split()[19],'name':name,'uid':12402,
                     'NoNewPrivs':status.get('NoNewPrivs','').strip(),'Seccomp':status.get('Seccomp','').strip(),'CapEff':status.get('CapEff','').strip()}
                if name in ['firefox','firefox-bin']:main.append(row)
                elif name in ['Web Content','Isolated Web Co']:content.append(row)
            except (FileNotFoundError,PermissionError,ProcessLookupError):pass
        return main,content
    try:
        assert command(['dpkg-query','-W','-f=${Version}','firefox'])['stdout']=='153.7.0esr-1+toddy1'
        report['default_target']=command(['systemctl','get-default']);assert report['default_target']['stdout'].strip()=='graphical.target'
        limit=time.monotonic()+75
        while time.monotonic()<limit:
            graphical=command(['systemctl','is-active','graphical.target']);gdm=command(['systemctl','is-active','gdm.service'])
            if graphical['stdout'].strip()==gdm['stdout'].strip()=='active':break
            time.sleep(1)
        assert graphical['stdout'].strip()==gdm['stdout'].strip()=='active','Default graphical/GDM boot failed; no manual start'
        report.update(graphical_target=graphical,automatic_gdm=gdm,kernel_commandline=Path('/proc/cmdline').read_text())
        report['networkmanager']=command(['systemctl','is-active','NetworkManager.service']);assert report['networkmanager']['stdout'].strip()=='active'
        server=subprocess.Popen(['python3',str(server_script)],user=12402,group=12402,extra_groups=[],cwd=fixture,
            env={'HOME':str(home),'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','PYTHONDONTWRITEBYTECODE':'1'},stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        deadline=time.monotonic()+660
        while time.monotonic()<deadline:
            if not owner:
                sessions=command(['loginctl','list-sessions','--no-legend','--no-pager'])
                for line in sessions['stdout'].splitlines():
                    sid=line.split()[0];values=command(['loginctl','show-session',sid,'-p','Class','-p','Type','-p','State','-p','Seat','-p','Name'])
                    props=dict(x.split('=',1) for x in values['stdout'].splitlines() if '=' in x)
                    if props.get('Class')=='user' and props.get('Name')==username and props.get('Type')=='wayland' and props.get('State')=='active' and props.get('Seat')=='seat0':owner={'session_id':sid,'properties':props}
            main,children=processes()
            if owner:
                for row in main:
                    identity={'pid':row['pid'],'start_ticks':row['start_ticks']}
                    if identity not in seen:
                        if stopped:reopened=True
                        seen.append(identity)
                if seen and not main:stopped=True
                states=command(['nmcli','-t','-f','TYPE,STATE','device','status'])['stdout']
                if 'ethernet:disconnected' in states or 'ethernet:unavailable' in states:network_off=True
            if select.select([transport],[],[],.5)[0]:
                message=transport.readline(128).decode().strip()
                if message=='DONE':finished=True;break
                if message.startswith('PHASE '):phases.append(message[6:])
            assert server.poll() is None,'Loopback fixture server exited'
        report.update(owner_session=owner,host_requested_finish=finished,ui_phase_annotations=phases,main_processes_seen=seen,
                      exit_between_launches=stopped,new_process_after_exit=reopened,network_off_observed=network_off)
        assert owner and finished and stopped and reopened,'Normal owner/open-close-reopen observation incomplete'
        required={'browser-open','input-verified','navigation-verified','restart-verified','tls-verified','offline-verified','stop-verified','responsive-verified'}
        assert required<=set(phases),'Native screenshot/interaction phases incomplete'
        events=[json.loads(line) for line in (home/'browser-http-events.jsonl').read_text().splitlines()]
        report['http_events']=events
        assert any(e.get('path')=='/' for e in events) and any(e.get('path','').startswith('/second.html') for e in events)
        assert any(e['event']=='slow-cancelled' for e in events),'Stop needs actual closed pending HTTP request'
        assert network_off,'Offline browser phase requires actual NIC state'
        limit=time.monotonic()+8
        while time.monotonic()<limit:
            main,children=processes()
            if children and all(c['NoNewPrivs']=='1' and c['Seccomp']=='2' and int(c['CapEff'],16)==0 for c in children):break
            time.sleep(.5)
        report.update(final_main=main,content_processes=children)
        assert main and children and all(c['NoNewPrivs']=='1' and c['Seccomp']=='2' and int(c['CapEff'],16)==0 for c in children),'Actual Web Content sandbox status incomplete'
        report['all_selected_exits_zero']=True
    except Exception as error:
        report.update(owner_session=owner,host_requested_finish=finished,ui_phase_annotations=phases,main_processes_seen=seen,
                      error={'type':type(error).__name__,'message':str(error)})
        report['diagnostics']=[command(a) for a in [['systemctl','status','gdm.service','graphical.target','--no-pager','-l'],['journalctl','-b','--no-pager','-n','100']]]
    finally:
        if server:
            server.terminate()
            try:server.wait(timeout=10)
            except subprocess.TimeoutExpired:server.kill();server.wait()
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
        raise AssertionError('Native browser gate failed; preserve report and scanout')


if __name__ == '__main__':
    main()

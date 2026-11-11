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
    assert Path('/home',username,'portal-allowed.txt').read_bytes()==b'Toddy native portal consent\n'
    import pwd
    assert pwd.getpwnam(username).pw_uid==12402
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
    import signal,traceback
    bootid=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    text=b'Toddy editor recovery proof\n'
    report={'scope':'Native existing-owner reboot persistence, offline Editor refusal/crash draft recovery/save and idle reference measurements. Fixture account only, no hardware/whole B02 acceptance.','kernel':os.uname().release,'boot_id':bootid,'schema_sha256':digest,'all_selected_exits_zero':False}
    owner=None;finished=False;phases=[];ready=False
    refusal=home/'refusal';assert not refusal.exists();refusal.mkdir(mode=0o555)
    protected=refusal/'read-only.txt';protected.write_bytes(b'Toddy protected original\n');protected.chmod(0o444)
    def service(args,timeout=35):
        r=command(args,timeout);assert r['exit']==0,r;return r
    def editor_pids():
        found=[]
        for p in Path('/proc').glob('[0-9]*'):
            try:
                if (p/'exe').readlink()==Path('/usr/bin/gnome-text-editor') and (p/'status').read_text().split('Uid:',1)[1].split()[0]=='12402':found.append(int(p.name))
            except (OSError,IndexError):pass
        return found
    def sample():
        assert not editor_pids(),'Close Editor before idle sample'
        before=list(map(int,Path('/proc/stat').read_text().splitlines()[0].split()[1:]));samples=[]
        for _ in range(3):
            time.sleep(5);mem={l.split(':')[0]:int(l.split()[1]) for l in Path('/proc/meminfo').read_text().splitlines() if l.startswith(('MemTotal:','MemAvailable:','SwapTotal:','SwapFree:'))}
            samples.append({'monotonic':time.monotonic(),'memory_kib':mem,'loadavg':Path('/proc/loadavg').read_text().strip()})
        after=list(map(int,Path('/proc/stat').read_text().splitlines()[0].split()[1:]));delta=[b-a for a,b in zip(before,after)];assert sum(delta)>0
        return {'scope':'15-second idle sample in virtual4CPU/4GiB normal owner session with Editor closed, networking offline and no agent/inference. Build target still contains sources; not final ISO size or physical benchmark.','samples':samples,'cpu_nonidle_percent':100*(1-(delta[3]+delta[4])/sum(delta)),'boot_time':command(['systemd-analyze','time'])}
    try:
        deadline=time.monotonic()+720
        while time.monotonic()<deadline:
            if not owner:
                for line in command(['loginctl','list-sessions','--no-legend','--no-pager'])['stdout'].splitlines():
                    sid=line.split()[0];r=command(['loginctl','show-session',sid,'-p','Class','-p','Type','-p','State','-p','Seat','-p','Name']);props=dict(l.split('=',1) for l in r['stdout'].splitlines() if '=' in l)
                    if props=={'Class':'user','Name':username,'Type':'wayland','State':'active','Seat':'seat0'}:owner={'session_id':sid,'properties':props}
                if owner:
                    until=time.monotonic()+30
                    while time.monotonic()<until and not Path('/run/user/12402/wayland-0').exists():time.sleep(.2)
                    assert Path('/run/user/12402/wayland-0').exists(),'Actual compositor readiness deadline'
                    persisted=user_command(['gsettings','get','org.gnome.desktop.interface','color-scheme']);assert persisted['exit']==0 and persisted['stdout'].strip()=="'prefer-dark'";report['previous_native_session_persisted']=persisted
                    accent=user_command(['gsettings','set','org.gnome.desktop.interface','accent-color','teal']);assert accent['exit']==0,accent
                    report['fixture_user_preference']='accent-color teal (differs from base blue); verify next boot'
                    report['nm_before_offline']=service(['nmcli','general','status'])
                    service(['nmcli','networking','off']);until=time.monotonic()+15
                    while time.monotonic()<until and json.loads(command(['ip','-j','route','show','default'])['stdout']):time.sleep(.2)
                    assert not json.loads(command(['ip','-j','route','show','default'])['stdout'])
                    report['offline_https']=user_command(['curl','--fail','--silent','--show-error','--connect-timeout','3','--max-time','5','--output','/dev/null','https://example.com/'],timeout=8);assert report['offline_https']['exit']!=0
                    report['offline_started']=True;ready=True;print('TODDY_EDITOR_OFFLINE_READY',flush=True)
            if select.select([transport],[],[],1)[0]:
                row=transport.readline(128).strip().decode()
                if row=='DONE':finished=True;break
                assert row.startswith('PHASE ');phase=row[6:];assert ready and phase not in phases;phases.append(phase)
                if phase=='editor-refusal':
                    assert protected.read_bytes()==b'Toddy protected original\n';report['protected_file_unchanged']=True
                elif phase=='editor-crash':
                    drafts=home/'.local/share/org.gnome.TextEditor/drafts';until=time.monotonic()+20;matches=[]
                    while time.monotonic()<until:
                        matches=[p for p in drafts.glob('*') if p.is_file() and p.read_bytes()==text]
                        if matches:break
                        time.sleep(.2)
                    assert len(matches)==1,'Exact actual autosaved draft missing; do not simulate recovery'
                    report['draft_before_crash']={'path':str(matches[0].relative_to(home)),'sha256':hashlib.sha256(text).hexdigest()}
                    pids=editor_pids();assert len(pids)==1,pids;os.kill(pids[0],signal.SIGKILL);until=time.monotonic()+10
                    while time.monotonic()<until and editor_pids():time.sleep(.2)
                    assert not editor_pids();report['intentional_fixture_crash']={'pid':pids[0],'signal':9,'process_exit_observed':True}
                elif phase=='editor-recovered':
                    saved=home/'editor-recovered.txt';assert saved.read_bytes()==text and saved.stat().st_uid==12402
                    report['recovered_saved_file_sha256']=hashlib.sha256(saved.read_bytes()).hexdigest()
                    assert protected.read_bytes()==b'Toddy protected original\n'
                elif phase=='editor-idle':report['idle']=sample()
                else:raise AssertionError('Unexpected editor phase '+phase)
        assert owner and finished and {'editor-refusal','editor-crash','editor-recovered','editor-idle'}<=set(phases)
        inventory=service(['dpkg-query','-W','-f=${binary:Package}\t${Version}\t${Architecture}\t${Depends}\n'])
        report['installed_packages']=[dict(zip(['name','version','architecture','depends'],line.split('\t',3))) for line in inventory['stdout'].splitlines()]
        report['agent_package_absent']=command(['dpkg-query','-W','toddy-agent']);assert report['agent_package_absent']['exit']!=0
        active=[]
        for p in Path('/proc').glob('[0-9]*'):
            try:
                name=(p/'comm').read_text().strip()
                if name in ['toddy-agent','ollama','llama-server','vllm','opencode']:active.append(name)
            except OSError:pass
        assert not active;report['active_agent_or_inference']=active
        service(['nmcli','networking','on']);until=time.monotonic()+40
        while time.monotonic()<until:
            routes=json.loads(command(['ip','-j','route','show','default'])['stdout'])
            if routes:break
            time.sleep(.5)
        assert routes;report['restored_routes']=routes
        assert Path('/etc/toddy/network/use-networkmanager').read_text()=='NetworkManager\n'
        persist=home/'b02-persistence.json';assert not persist.exists()
        persist.write_text(json.dumps({'boot_id':bootid,'saved_file_sha256':report['recovered_saved_file_sha256'],'accent_color':'teal','color_scheme':'prefer-dark','network_manager':'NetworkManager','protected_sha256':hashlib.sha256(protected.read_bytes()).hexdigest()},indent=2)+'\n');persist.chmod(0o644);os.chown(persist,12402,12402)
        report.update(owner_session=owner,ui_phase_annotations=phases,persistence_marker_sha256=hashlib.sha256(persist.read_bytes()).hexdigest(),all_selected_exits_zero=True)
    except Exception as error:
        report.update(owner_session=owner,host_requested_finish=finished,ui_phase_annotations=phases,error={'type':type(error).__name__,'message':str(error)},traceback=traceback.format_exc())
        report['diagnostics']=command(['journalctl','-b','--no-pager','-n','100'])
    finally:
        transport.close();report['gdm_stop']=command(['systemctl','stop','gdm.service'],timeout=40)
        report['schema_unchanged']=hashlib.sha256(cache.read_bytes()).hexdigest()==digest
        report['all_selected_exits_zero'] &= report['gdm_stop']['exit']==0 and report['schema_unchanged']
    raw=json.dumps(report,sort_keys=True).encode();encoded=base64.b64encode(zlib.compress(raw,9)).decode();chunks=[encoded[i:i+1024] for i in range(0,len(encoded),1024)]
    fd=os.open('/dev/ttyS1',os.O_WRONLY|os.O_NOCTTY);attrs=termios.tcgetattr(fd);attrs[0]=attrs[1]=attrs[3]=0;attrs[2]|=termios.CLOCAL|termios.CREAD;attrs[4]=attrs[5]=termios.B115200;termios.tcsetattr(fd,termios.TCSANOW,attrs)
    with os.fdopen(fd,'w',buffering=1) as evidence:
        for i,chunk in enumerate(chunks):print('TODDY_B02_RUNTIME_DATA',i,chunk,file=evidence,flush=True)
        print('TODDY_B02_RUNTIME_RESULT',json.dumps({'kernel':os.uname().release,'all_selected_exits_zero':report['all_selected_exits_zero'],'report_sha256':hashlib.sha256(raw).hexdigest(),'chunks':len(chunks)}),file=evidence,flush=True);termios.tcdrain(evidence.fileno())
    if not report['all_selected_exits_zero']:raise AssertionError('Native offline/editor/persistence preparation failed')

if __name__=='__main__':main()

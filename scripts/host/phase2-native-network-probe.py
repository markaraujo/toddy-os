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
    def snapshot():
        rows=command(['nmcli','-t','-f','DEVICE,TYPE,STATE','device','status'])
        ethernet=[line.split(':',2) for line in rows['stdout'].splitlines() if ':ethernet:' in line]
        if not ethernet:return {'interface':None,'state':None,'status':rows}
        interface=ethernet[0][0]
        state=command(['nmcli','-g','GENERAL.STATE','device','show',interface])
        match=re.match(r'(\d+)',state['stdout'])
        return {'interface':interface,'state':int(match.group(1)) if match else None,'status':ethernet[0][2]}
    def connectivity(interface):
        address=command(['ip','-j','address','show','dev',interface])
        routes=command(['ip','-j','route','show','default'])
        dns=command(['nmcli','-g','IP4.DNS','device','show',interface])
        dhcp=command(['nmcli','-g','DHCP4.OPTION','device','show',interface])
        flush=command(['resolvectl','flush-caches'])
        resolved=user_command(['getent','ahostsv4','example.com'])
        assert all(r['exit']==0 for r in [address,routes,dns,dhcp,flush,resolved])
        assert any(a['family']=='inet' for row in json.loads(address['stdout']) for a in row['addr_info'])
        assert any(row.get('dev')==interface and row.get('gateway') for row in json.loads(routes['stdout']))
        assert dns['stdout'].strip() and dhcp['stdout'].strip() and resolved['stdout'].strip()
        return {'address':address,'default_routes':routes,'dns':dns,'dhcp':dhcp,'resolved_public_name':resolved}
    report={'scope':'Native normal-owner GNOME Network UI on/off/reconnect, actual NM DHCP/DNS/public HTTPS and noninteractive active-client polkit; stop-before-switch networkd recovery in disposable overlay. No physical networking/Wi-Fi/whole B02 acceptance.',
        'kernel':os.uname().release,'schema_sha256':digest,'all_selected_exits_zero':False,'runs':[]}
    owner=None;requested_finish=False;transitions={'connected':False,'off_after_connected':False,'reconnected':False};observations=[]
    try:
        assert Path('/etc/toddy/network/use-networkmanager').read_text()=='NetworkManager\n'
        for args in [['systemctl','start','dbus.service','systemd-logind.service','systemd-userdbd.service'],
                     ['udevadm','settle','--timeout=20'],['systemctl','start','gdm.service']]:
            report['runs'].append(command(args,timeout=45))
        deadline=time.monotonic()+600;last=None
        while time.monotonic()<deadline:
            sessions=command(['loginctl','list-sessions','--no-legend','--no-pager'])
            for line in sessions['stdout'].splitlines():
                sid=line.split()[0]
                values=command(['loginctl','show-session',sid,'-p','Class','-p','Type','-p','State','-p','Seat','-p','Name'])
                props=dict(s.split('=',1) for s in values['stdout'].splitlines() if '=' in s)
                if props.get('Class')=='user' and props.get('Name')==username and props.get('Type')=='wayland' and props.get('State')=='active' and props.get('Seat')=='seat0':owner={'session_id':sid,'properties':props}
            state=snapshot()
            if state!=last:observations.append({'monotonic':time.monotonic(),**state});last=state
            if owner:
                if state['state']==100:
                    if transitions['off_after_connected']:transitions['reconnected']=True
                    transitions['connected']=True
                elif transitions['connected'] and state['state'] in [20,30]:transitions['off_after_connected']=True
            if select.select([transport],[],[],1)[0]:
                requested_finish=transport.readline(64)==b'DONE\n';break
            if command(['systemctl','is-failed','gdm.service'])['stdout'].strip()=='failed':break
        report.update(owner_session=owner,host_requested_finish=requested_finish,transitions=transitions,observations=observations)
        assert owner is not None and requested_finish and all(transitions.values()),'Actual owner UI connection transitions incomplete'
        state=snapshot();assert state['state']==100 and state['interface'];interface=state['interface']
        report['nm_active']=command(['systemctl','is-active','NetworkManager.service']);assert report['nm_active']['stdout'].strip()=='active'
        report['networkd_inactive']=command(['systemctl','is-active','systemd-networkd.service']);assert report['networkd_inactive']['stdout'].strip()=='inactive'
        report['resolved_active']=command(['systemctl','is-active','systemd-resolved.service']);assert report['resolved_active']['stdout'].strip()=='active'
        clients=[]
        for p in Path('/proc').iterdir():
            if not p.name.isdigit():continue
            try:
                if p.stat().st_uid==12402 and (p/'exe').resolve()==Path('/usr/bin/gnome-control-center'):clients.append(p)
            except (FileNotFoundError,PermissionError):pass
        assert len(clients)==1,'Require actual active Settings process'
        client=clients[0];start=(client/'stat').read_text().split()[21]
        report['active_settings_client']={'pid':int(client.name),'start_ticks':start,'uid':12402}
        permissions=[]
        for action in ['org.freedesktop.NetworkManager.network-control','org.freedesktop.NetworkManager.enable-disable-network']:
            result=user_command(['pkcheck','--action-id',action,'--process',f'{client.name},{start},12402'])
            permissions.append(result);assert result['exit']==0
        report['actual_client_policy']=permissions
        report['nm_connectivity']=connectivity(interface)
        report['public_https']=user_command(['curl','--fail','--silent','--show-error','--proto','=https','--connect-timeout','10','--max-time','20','--output','/dev/null','--write-out','%{http_code}','https://example.com/'],timeout=25)
        assert report['public_https']['exit']==0 and report['public_https']['stdout']=='200'
        marker=Path('/etc/toddy/network/use-networkmanager');backup=marker.with_name('use-networkmanager.native-test-backup');assert not backup.exists()
        recovery=[]
        def service(args):
            result=command(args,timeout=40);recovery.append(result);assert result['exit']==0,result
        service(['systemctl','stop','NetworkManager.service']);marker.rename(backup)
        lease=Path('/run/systemd/netif/leases')/Path('/sys/class/net',interface,'ifindex').read_text().strip()
        assert not lease.exists(),'networkd was not the selected initial manager'
        service(['systemctl','start','systemd-networkd.service'])
        limit=time.monotonic()+40
        while time.monotonic()<limit:
            result=command(['ip','-j','route','show','default'])
            if lease.exists() and any(r.get('dev')==interface and r.get('gateway') for r in json.loads(result['stdout'])):break
            time.sleep(1)
        assert lease.is_file() and any(r.get('dev')==interface and r.get('gateway') for r in json.loads(result['stdout']))
        text=lease.read_text();assert all(k in text for k in ['ADDRESS=','ROUTER=','DNS='])
        report['new_networkd_lease']={'sha256':hashlib.sha256(lease.read_bytes()).hexdigest(),'fresh_in_this_boot':True,'address_router_dns_fields':True}
        assert command(['systemctl','is-active','systemd-networkd.service'])['stdout'].strip()=='active'
        assert command(['systemctl','is-active','NetworkManager.service'])['stdout'].strip()=='inactive'
        assert command(['resolvectl','flush-caches'])['exit']==0
        report['networkd_recovery_dns']=user_command(['getent','ahostsv4','example.com']);assert report['networkd_recovery_dns']['exit']==0 and report['networkd_recovery_dns']['stdout'].strip()
        service(['systemctl','stop','systemd-networkd.service']);backup.rename(marker)
        service(['systemctl','start','NetworkManager.service'])
        limit=time.monotonic()+40
        while time.monotonic()<limit and snapshot()['state']!=100:time.sleep(1)
        assert snapshot()['state']==100
        assert command(['systemctl','is-active','systemd-networkd.service'])['stdout'].strip()=='inactive'
        report['restored_nm_connectivity']=connectivity(interface);report['manager_recovery']=recovery
        assert marker.read_text()=='NetworkManager\n' and not backup.exists()
        report['all_selected_exits_zero']=all(r['exit']==0 for r in report['runs'])
    except Exception as error:
        report.update(owner_session=owner,host_requested_finish=requested_finish,transitions=transitions,observations=observations)
        report['error']={'type':type(error).__name__,'message':str(error)}
        report['diagnostics']=[command(a) for a in [['systemctl','status','NetworkManager.service','systemd-networkd.service','systemd-resolved.service','--no-pager','-l'],['nmcli','device','status'],['ip','-j','route'],['resolvectl','status'],['journalctl','-b','-u','NetworkManager.service','--no-pager','-n','100']]]
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
        raise AssertionError('Native network gate failed; preserve report and scanout')


if __name__ == '__main__':
    main()

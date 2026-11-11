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


REUSED_NETWORK_PREFIX = None

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
    report={'scope':'Remaining native manager recovery after actual reboot of retained first disposable overlay. Earlier normal GDM/GUI/DNS/HTTPS/polkit proof reused explicitly; no GUI/state writes replayed.',
        'kernel':os.uname().release,'schema_sha256':digest,'all_selected_exits_zero':False,'runs':[],'reused_prefix':REUSED_NETWORK_PREFIX}
    def service(args):
        r=command(args,timeout=40);report['runs'].append(r);assert r['exit']==0,r
    def dns():
        service(['resolvectl','flush-caches'])
        r=command(['getent','ahostsv4','example.com']);assert r['exit']==0 and r['stdout'].strip();return r
    marker=Path('/etc/toddy/network/use-networkmanager');backup=marker.with_name('use-networkmanager.native-test-backup')
    try:
        assert REUSED_NETWORK_PREFIX and not marker.exists() and backup.read_text()=='NetworkManager\n','Require retained actual stopped/recovery selection before any write'
        limit=time.monotonic()+45;lease=None;interface=None
        while time.monotonic()<limit:
            links=[p.name for p in Path('/sys/class/net').iterdir() if p.name!='lo']
            if len(links)==1:
                interface=links[0]
                lease=command(['networkctl','--json=short','dhcp-lease',interface])
                if lease['exit']==0:break
            time.sleep(1)
        assert interface and lease and lease['exit']==0,lease
        parsed=json.loads(lease['stdout']);assert isinstance(parsed,dict) and parsed
        report['actual_networkd_lease']=lease
        report['persisted_recovery_selection_after_reboot']=True
        active=command(['systemctl','is-active','systemd-networkd.service']);inactive=command(['systemctl','is-active','NetworkManager.service'])
        assert active['stdout'].strip()=='active' and inactive['stdout'].strip()=='inactive'
        report['networkd_active']=active;report['nm_inactive']=inactive
        address=command(['ip','-j','address','show','dev',interface]);route=command(['ip','-j','route','show','default'])
        assert address['exit']==route['exit']==0
        assert any(a['family']=='inet' for row in json.loads(address['stdout']) for a in row['addr_info'])
        assert any(row.get('dev')==interface and row.get('gateway') for row in json.loads(route['stdout']))
        report['networkd_address']=address;report['networkd_routes']=route;report['networkd_public_dns']=dns()
        # Continue the known retained state, never repeat the already completed NM stop/networkd start.
        service(['systemctl','stop','systemd-networkd.service']);backup.rename(marker)
        service(['systemctl','start','NetworkManager.service'])
        limit=time.monotonic()+45;state=None
        while time.monotonic()<limit:
            state=command(['nmcli','-g','GENERAL.STATE','device','show',interface])
            if state['exit']==0 and state['stdout'].startswith('100 '):break
            time.sleep(1)
        assert state and state['exit']==0 and state['stdout'].startswith('100 '),state
        assert command(['systemctl','is-active','systemd-networkd.service'])['stdout'].strip()=='inactive'
        assert command(['systemctl','is-active','NetworkManager.service'])['stdout'].strip()=='active'
        report['restored_nm_state']=state
        options=command(['nmcli','-g','DHCP4.OPTION','device','show',interface]);assert options['exit']==0 and options['stdout'].strip()
        report['restored_nm_dhcp']=options;report['restored_nm_public_dns']=dns()
        assert marker.read_text()=='NetworkManager\n' and not backup.exists()
        report['all_selected_exits_zero']=True
    except Exception as error:
        report['error']={'type':type(error).__name__,'message':str(error)}
        report['diagnostics']=[command(a) for a in [['systemctl','status','NetworkManager.service','systemd-networkd.service','systemd-resolved.service','--no-pager','-l'],['networkctl','--json=short','status'],['ip','-j','route'],['resolvectl','status']]]
    finally:
        report['schema_unchanged']=hashlib.sha256(cache.read_bytes()).hexdigest()==digest
        report['all_selected_exits_zero'] &= report['schema_unchanged']
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

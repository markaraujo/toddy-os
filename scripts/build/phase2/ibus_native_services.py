"""Run owned IBus services with private user data/buses and no external route."""
from pathlib import Path
import hashlib,json,os,shutil,signal,subprocess,time
ROOT=Path('/opt/toddy-build');TARGET=Path('/mnt/lfs');LOG=Path('/var/log/toddy/phase2')
receipt=LOG/'ibus-installed-services-4.json';work=TARGET/'tmp/toddy-ibus-installed-services-4';virtual='/tmp/'+work.name
assert not receipt.exists() and not work.exists(),'Inspect actual private state before any replay'
step=json.loads(Path('/var/log/toddy/build/b02-ibus-schema-union-install.success.json').read_text());assert step['recipe_exit']==step['postcheck_exit']==0
# Namespace-local standard devices, matching the qualified NSS native profile.
subprocess.run(['mount','-t','tmpfs','-o','nosuid,size=1m,mode=755','tmpfs',str(TARGET/'dev')],check=True)
for name in ['null','zero','random','urandom']:
    p=TARGET/'dev'/name;p.touch();subprocess.run(['mount','--bind','/dev/'+name,str(p)],check=True)
subprocess.run(['ip','link','set','lo','up'],check=True)
assert not json.loads(subprocess.check_output(['ip','-j','route'],text=True))
assert {r['ifname'] for r in json.loads(subprocess.check_output(['ip','-j','link'],text=True))}=={'lo'}
work.mkdir(mode=0o700);os.chown(work,101,101)
for name in ['home','config','cache','data','runtime']:
    p=work/name;p.mkdir(mode=0o700);os.chown(p,101,101)
script=work/'client.py';shutil.copyfile(ROOT/'scripts/build/phase2/ibus-service-client.py',script);script.chmod(0o444)
env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','PYTHONDONTWRITEBYTECODE':'1','HOME':virtual+'/home','XDG_CONFIG_HOME':virtual+'/config','XDG_CACHE_HOME':virtual+'/cache','XDG_DATA_HOME':virtual+'/data','XDG_RUNTIME_DIR':virtual+'/runtime','GSETTINGS_BACKEND':'memory','IBUS_ADDRESS_FILE':virtual+'/cache/ibus-address'}
def private_processes():
    rows={}
    for p in Path('/proc').iterdir():
        if not p.name.isdigit():continue
        try:
            if p.stat().st_uid!=101:continue
            e=(p/'environ').read_bytes().split(b'\0')
            if ('XDG_CONFIG_HOME='+env['XDG_CONFIG_HOME']).encode() not in e:continue
            fields=(p/'stat').read_text().split()
            if fields[2]!='Z':rows[int(p.name)]={'start':fields[21],'command':(p/'comm').read_text().strip()}
        except (FileNotFoundError,ProcessLookupError,PermissionError):continue
    return rows
def cleanup():
    before=private_processes()
    for pid,row in before.items():
        if private_processes().get(pid)==row:os.kill(pid,signal.SIGTERM)
    until=time.monotonic()+5
    while private_processes() and time.monotonic()<until:time.sleep(0.05)
    assert not private_processes(),'Private services still active; preserve state, no replay'
    return before
records=[]
try:
    for mode in ['first','reconnect']:
        command=['chroot','--userspec=101:101',str(TARGET),'dbus-run-session','--','python3','-B',virtual+'/client.py',mode,virtual]
        proc=subprocess.Popen(command,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
        try:out,error=proc.communicate(timeout=60)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid,signal.SIGTERM);out,error=proc.communicate(timeout=10)
            (LOG/('ibus-services-4-'+mode+'-timeout.log')).write_text(out+error)
            raise AssertionError('Native service client timed out; not success')
        (LOG/('ibus-services-4-'+mode+'.stdout')).write_text(out);(LOG/('ibus-services-4-'+mode+'.stderr')).write_text(error)
        (LOG/('ibus-services-4-'+mode+'.exit')).write_text(str(proc.returncode)+'\n')
        leftovers=cleanup();assert proc.returncode==0,error[-1200:]
        records.append({'mode':mode,'exit':proc.returncode,'result':json.loads(out),'private_services_terminated_after_bus_close':list(leftovers.values())})
    assert records[0]['result']['bus_guid']!=records[1]['result']['bus_guid']
    result={'scope':'Actual installed IBus simple engine/private input context/default dead-key Compose IPC commit, pre-cancelled read/refusal/recovery/Stop and distinct reconnected session bus. No build module/library/schema overrides, real accounts, external route or GNOME GUI/hardware acceptance.','records':records,'uid':101,'network_interfaces':['lo'],'external_routes':0,'private_process_cleanup_verified':True,'private_profile_removed':True}
    assert not private_processes();shutil.rmtree(work)
    receipt.write_text(json.dumps(result,indent=2)+'\n')
except BaseException:
    cleanup()
    raise

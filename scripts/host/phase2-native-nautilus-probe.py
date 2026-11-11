"""Normal authenticated native user-seat tests with exact readonly Nautilus cache."""
from pathlib import Path
import base64
import ctypes
import hashlib
import json
import os
import re
import resource
import select
import signal
import stat
import subprocess
import tempfile
import termios
import time
import zlib

NAUTILUS_FIXTURE = None
REUSED_NAUTILUS = None


def digest(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def command(args,timeout=25):
    r=subprocess.run(args,capture_output=True,text=True,timeout=timeout)
    return {'args':args,'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr}


def restore_inputs():
    fixture_path=Path('/sources/phase2/native-fixtures/nautilus-1.json')
    assert fixture_path.stat().st_uid==0 and not fixture_path.is_symlink()
    assert digest(fixture_path)==NAUTILUS_FIXTURE['fixture_sha256']
    fixture=json.loads(fixture_path.read_text());assert fixture['state']=='complete'
    transport=fixture['transport'];assert transport['device_serial']=='TODDY-NAUTILUS-INPUT'
    device=Path('/dev/disk/by-id/virtio-TODDY-NAUTILUS-INPUT').resolve(strict=True)
    assert stat.S_ISBLK(device.stat().st_mode)
    assert command(['lsblk','-dnro','SERIAL',str(device)])['stdout'].strip()==transport['device_serial']
    assert command(['blockdev','--getro',str(device)])['stdout'].strip()=='1'
    assert int(command(['blockdev','--getsize64',str(device)])['stdout'])==transport['raw_bytes']
    cache=Path('/run/toddy-nautilus-native-cache-1');assert not cache.exists();cache.mkdir(mode=0o700)
    subprocess.run(['mount','-t','tmpfs','-o','size=384M,mode=0700,nosuid,nodev','toddy-nautilus-native-input',str(cache)],check=True)
    archive=cache/'transport.tar.gz';raw_hash=hashlib.sha256();archive_hash=hashlib.sha256()
    with device.open('rb') as src,archive.open('xb') as dst:
        remaining=transport['archive_bytes']
        while remaining:
            block=src.read(min(8*1024**2,remaining));assert block
            remaining-=len(block);archive_hash.update(block);raw_hash.update(block);dst.write(block)
        pad=src.read(transport['raw_bytes']-transport['archive_bytes']);assert not any(pad);raw_hash.update(pad)
    assert archive_hash.hexdigest()==transport['archive_sha256'] and raw_hash.hexdigest()==transport['raw_sha256']
    subprocess.run(['tar','--extract','--gzip','--file='+str(archive),'--directory='+str(cache),'--numeric-owner','--same-owner','--acls','--xattrs','--sparse'],check=True)
    expected=fixture['cache_entries'];actual=set()
    for prefix in ['nautilus-input-1','nautilus-work-1']:
        actual.add(prefix);actual.update(str(p.relative_to(cache)) for p in (cache/prefix).rglob('*'))
    assert actual==set(expected)
    forward={};reverse={}
    for name,row in expected.items():
        p=cache/name;assert not Path(name).is_absolute() and '..' not in Path(name).parts
        os.utime(p,ns=(row['mtime_ns'],row['mtime_ns']),follow_symlinks=False)
        s=p.lstat();assert (s.st_mode,s.st_uid,s.st_gid)==(row['mode'],row['uid'],row['gid'])
        if row['type']=='file':
            assert s.st_size==row['bytes'] and digest(p)==row['sha256']
            old=tuple(row['hardlink_identity']);new=(s.st_dev,s.st_ino)
            assert forward.setdefault(old,new)==new and reverse.setdefault(new,old)==old
        elif row['type']=='symlink':assert os.readlink(p)==row['target']
        else:assert row['type']=='directory' and stat.S_ISDIR(s.st_mode)
    source=cache/'nautilus-input-1/nautilus-50.2.2';work=cache/'nautilus-work-1'
    for src,dst in [(source,Path(fixture['source_path'])),(work,Path(fixture['work_path'])),(source,Path('/src')),(work,Path('/build'))]:
        if not dst.exists():dst.mkdir()
        assert dst.is_dir() and not dst.is_symlink() and not list(dst.iterdir())
        subprocess.run(['mount','--bind',str(src),str(dst)],check=True)
        subprocess.run(['mount','-o','remount,bind,ro,nosuid,nodev',str(dst)],check=True)
        assert dst.stat().st_ino==src.stat().st_ino
    archive.unlink()
    return fixture,{'state':'complete','archive_sha256':transport['archive_sha256'],'readonly_device':True,'verified_entries':len(expected),'exact_source_compile_stage_restored':True,'source_work_bindings_readonly':True}


def run_original_tests(fixture,uid):
    runtime=Path('/run/user')/str(uid)
    assert runtime.stat().st_uid==uid and stat.S_IMODE(runtime.stat().st_mode)==0o700
    waylands=[p for p in runtime.glob('wayland-*') if p.is_socket()]
    assert len(waylands)==1 and (runtime/'bus').is_socket()
    desktop={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','PYTHONDONTWRITEBYTECODE':'1',
             'XDG_RUNTIME_DIR':str(runtime),'DBUS_SESSION_BUS_ADDRESS':'unix:path='+str(runtime/'bus'),
             'WAYLAND_DISPLAY':str(waylands[0]),'XDG_SESSION_TYPE':'wayland','XDG_CURRENT_DESKTOP':'GNOME'}
    def nnp():
        assert os.geteuid()==uid and ctypes.CDLL(None,use_errno=True).prctl(38,1,0,0,0)==0
    reused=REUSED_NAUTILUS['reused_runs'] if REUSED_NAUTILUS else []
    assert [r['name'] for r in reused]==[r['name'] for r in fixture['selected_tests'][:len(reused)]]
    assert all(r['passed'] and r['exit']==0 and not r['timed_out'] for r in reused)
    rows=[];started=time.monotonic();positive=None
    with tempfile.TemporaryDirectory(prefix='toddy-nautilus-native-',dir='/var/tmp') as directory:
        base=Path(directory);os.chown(base,uid,uid)
        for index,test in enumerate(fixture['selected_tests'][len(reused):],start=len(reused)):
            home=base/('case-'+str(index));home.mkdir(mode=0o700);os.chown(home,uid,uid)
            env=dict(desktop);env.update(test['env'])
            env.update(HOME=str(home),XDG_CONFIG_HOME=str(home/'config'),XDG_CACHE_HOME=str(home/'cache'),XDG_DATA_HOME=str(home/'data'),TMPDIR='/tmp',PYTHONDONTWRITEBYTECODE='1')
            if positive is None:
                code="""from pathlib import Path
import json,os
s=Path('/proc/self/status').read_text().splitlines()
assert all(next(x for x in s if x.startswith(k)).split()[1]=='0000000000000000' for k in ['CapEff:','CapPrm:'])
assert next(x for x in s if x.startswith('NoNewPrivs:')).split()[1]=='1'
p=Path.home()/'allowed';p.write_text('private');assert p.read_text()=='private';p.unlink()
for path in ['/src/.toddy-denied','/build/compile/.toddy-denied']:
 try:Path(path).write_text('denied')
 except OSError as error:assert error.errno==30
 else:raise AssertionError('Readonly input unexpectedly writable')
print(json.dumps({'UID':os.geteuid(),'NoNewPrivs':True,'effective_permitted_caps_zero':True,'private_home_rw':True,'source_compile_writes_denied':True}))
"""
                p=subprocess.run(['python3','-B','-c',code],user=uid,group=uid,extra_groups=[],preexec_fn=nnp,env=env,cwd='/build/compile',capture_output=True,text=True,timeout=15)
                positive={'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr};assert p.returncode==0,positive
            remaining=fixture['focused_budget']['whole_selected_seconds']-(time.monotonic()-started)
            if remaining<=0:break
            timeout=min(fixture['focused_budget']['per_program_seconds'],remaining)
            begun=time.monotonic();p=subprocess.Popen(test['cmd'],user=uid,group=uid,extra_groups=[],preexec_fn=nnp,env=env,cwd='/build/compile',stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,start_new_session=True)
            timed_out=False
            try:stdout,stderr=p.communicate(timeout=timeout)
            except subprocess.TimeoutExpired:
                timed_out=True;os.killpg(p.pid,signal.SIGTERM)
                try:stdout,stderr=p.communicate(timeout=5)
                except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);stdout,stderr=p.communicate(timeout=5)
            row={'name':test['name'],'command':test['cmd'],'exit':p.returncode,'timed_out':timed_out,'elapsed_seconds':round(time.monotonic()-begun,3),'stdout':stdout,'stderr':stderr}
            if test['name']=='test-nautilus-search-engine-simple':
                hits=re.findall(r'^Hit [0-9]+: (file://[^\n]+)$',stdout,re.M)
                expected={'engine_simple','engine_simple_directory','engine_simple_second_directory'}
                row.update(passed=p.returncode==0 and not timed_out and len(hits)==len(set(hits))==3 and {h.rsplit('/',1)[-1] for h in hits}==expected and '\nNautilus search engine simple finished!\n' in stdout,search_hits=hits,source_asserted_total_hits=3,source_backed_non_TAP_driver=True)
            elif test['name']=='test-nautilus-directory-async':
                row.update(passed=p.returncode==0 and not timed_out and 'loading file:///tmp' in stdout and 'done loading\n' in stdout,async_completion_observed='done loading\n' in stdout,source_backed_non_TAP_driver=True)
            elif test['name']=='validate-appdata':
                row.update(passed=p.returncode==0 and not timed_out,metadata_validation_only=True)
            else:
                plans=re.findall(r'^1[.][.]([0-9]+)\s*$',stdout,re.M)
                cases=re.findall(r'^(ok|not ok)\s+([0-9]+)\b([^\n]*)',stdout,re.M)
                plan=int(plans[-1]) if plans else 0
                skipped=sum('SKIP' in tail.upper() for _,_,tail in cases)
                row.update(planned_cases=plan,observed_cases=len(cases),skipped_cases=skipped,passed_cases=sum(kind=='ok' and 'SKIP' not in tail.upper() for kind,_,tail in cases))
                row['passed']=p.returncode==0 and not timed_out and plan>0 and len(cases)==plan and skipped==0 and all(kind=='ok' for kind,_,_ in cases)
            rows.append(row)
            if not row['passed']:break
    for base,key in [(Path(fixture['source_path']),'source_files'),(Path(fixture['work_path'])/'compile','compile_files'),(Path(fixture['work_path'])/'stage','stage_files')]:
        actual={str(p.relative_to(base)):digest(p) for p in base.rglob('*') if p.is_file() and not p.is_symlink()};assert actual==fixture[key]
    return {'all_selected_passed':len(rows)+len(reused)==len(fixture['selected_tests']) and all(r['passed'] for r in rows),'positive_control':positive,'programs_executed':len(rows),'programs_reused':len(reused),'programs_total':len(rows)+len(reused),'expected_programs':len(fixture['selected_tests']),'new_passed_GLib_cases':sum(r.get('passed_cases',0) for r in rows),'reused_passed_GLib_cases':sum(r.get('passed_cases',0) for r in reused),'qualified_prefix':REUSED_NAUTILUS,'skipped_cases':sum(r.get('skipped_cases',0) for r in rows),'runs':rows,'readonly_inputs_unchanged':True,'not_selected':fixture['not_selected']}


def main():
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    assert os.geteuid()==0 and os.uname().release=='7.1.8-toddy'
    assert Path('/proc/1/comm').read_text().strip()=='systemd'
    device=command(['findmnt','-n','-o','SOURCE','/'])['stdout'].strip();assert re.fullmatch('/dev/[a-z0-9]+',device)
    parent=command(['lsblk','-ndo','PKNAME',device])['stdout'].strip()
    assert command(['lsblk','-dnro','SERIAL','/dev/'+parent])['stdout'].strip()=='TODDY-BOOT-TEST'
    assert command(['dpkg-query','-W','-f=${Version}','gtk'])['stdout']=='4.22.4-1+toddy11'
    cache=Path('/usr/share/glib-2.0/schemas/gschemas.compiled');cache_sha=digest(cache)
    assert cache_sha=='5ae3337c3e495d50e464e2f8acbc0f6a1652034dabe4eb24f9c79b6d38883acf'
    fixture,input_proof=restore_inputs()
    fd=os.open('/dev/ttyS2',os.O_RDWR|os.O_NOCTTY);attrs=termios.tcgetattr(fd);attrs[0]=attrs[1]=attrs[3]=0
    attrs[2]|=termios.CLOCAL|termios.CREAD;attrs[4]=attrs[5]=termios.B115200;termios.tcsetattr(fd,termios.TCSANOW,attrs)
    transport=os.fdopen(fd,'r+b',buffering=0);transport.write(b'READY\n')
    assert select.select([transport],[],[],90)[0],'Private fixture channel missing'
    credential=transport.readline(64).strip();assert re.fullmatch(b'[a-z]{24}',credential)
    username='toddy-preview';uid=12402
    assert not Path('/home',username).exists()
    subprocess.run(['useradd','-m','-U','-u',str(uid),'-c','Toddy Preview','-s','/bin/bash',username],check=True,capture_output=True,timeout=20)
    changed=subprocess.run(['chpasswd','-c','SHA512'],input=username.encode()+b':'+credential+b'\n',capture_output=True,timeout=20);credential=None
    assert changed.returncode==0,'Private account configuration failed'
    transport.write(b'CONFIGURED\n')
    report={'scope':'Native Nautilus original focused test programs on a normal GDM/PAM authenticated Wayland user seat, exact readonly source/compiler/stage restored from readonly data device. Not an installed Nautilus application/GUI, full-suite, physical or B02 pass.','kernel':os.uname().release,'pid1':'systemd','input_transport':input_proof,'all_selected_exits_zero':False,'runs':[]}
    try:
        for args in [['systemctl','start','dbus.service','systemd-logind.service','systemd-userdbd.service'],['udevadm','settle','--timeout=20'],['systemctl','start','gdm.service']]:report['runs'].append(command(args,timeout=45))
        deadline=time.monotonic()+180;owner=None;finished=False
        while time.monotonic()<deadline:
            for line in command(['loginctl','list-sessions','--no-legend','--no-pager'])['stdout'].splitlines():
                session=line.split()[0];r=command(['loginctl','show-session',session,'-p','Class','-p','Type','-p','State','-p','Seat','-p','Name'])
                properties=dict(l.split('=',1) for l in r['stdout'].splitlines() if '=' in l)
                if properties.get('Class')=='user' and properties.get('Name')==username and properties.get('Seat')=='seat0' and properties.get('Type')=='wayland' and properties.get('State')=='active':owner={'session_id':session,'properties':properties}
            if select.select([transport],[],[],1)[0]:finished=transport.readline(64)==b'DONE\n';break
            if command(['systemctl','is-failed','gdm.service'])['stdout'].strip()=='failed':break
        report['owner_session']=owner;report['host_requested_tests']=finished
        if owner and finished:report['original_tests']=run_original_tests(fixture,uid)
        report['all_selected_exits_zero']=owner is not None and finished and report.get('original_tests',{}).get('all_selected_passed',False) and all(r['exit']==0 for r in report['runs'])
    except Exception as error:report['error']={'type':type(error).__name__,'message':str(error)}
    finally:
        transport.close();report['gdm_stop']=command(['systemctl','stop','gdm.service'],timeout=40)
        report['schema_unchanged']=digest(cache)==cache_sha
        report['all_selected_exits_zero'] &= report['gdm_stop']['exit']==0 and report['schema_unchanged']
    raw=json.dumps(report,sort_keys=True).encode();assert len(raw)<4*1024**2
    encoded=base64.b64encode(zlib.compress(raw,9)).decode();chunks=[encoded[i:i+1024] for i in range(0,len(encoded),1024)]
    fd=os.open('/dev/ttyS1',os.O_WRONLY|os.O_NOCTTY);attrs=termios.tcgetattr(fd);attrs[0]=attrs[1]=attrs[3]=0;attrs[2]|=termios.CLOCAL|termios.CREAD;attrs[4]=attrs[5]=termios.B115200;termios.tcsetattr(fd,termios.TCSANOW,attrs)
    with os.fdopen(fd,'w',buffering=1) as evidence:
        for i,chunk in enumerate(chunks):print('TODDY_B02_RUNTIME_DATA',i,chunk,file=evidence,flush=True)
        print('TODDY_B02_RUNTIME_RESULT',json.dumps({'kernel':os.uname().release,'all_selected_exits_zero':report['all_selected_exits_zero'],'report_sha256':hashlib.sha256(raw).hexdigest(),'chunks':len(chunks)}),file=evidence,flush=True);termios.tcdrain(evidence.fileno())
    assert report['all_selected_exits_zero'],'Native Nautilus selected original test gate failed; retain report'


if __name__=='__main__':
    try:main()
    except Exception as error:
        print('TODDY_B02_RUNTIME_FAIL',type(error).__name__,str(error),flush=True)
        raise

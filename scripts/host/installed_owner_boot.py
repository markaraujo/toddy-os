#!/usr/bin/env python3
"""Two real installed-owner cold boots plus separate text recovery observation.

Source-only coordinator. Existing contexts are never restarted automatically.
Only a self-contained private disposable installed disk is accepted as backing.
"""
import argparse,fcntl,getpass,hashlib,json,os,re,resource,socket,stat,subprocess,sys,time,uuid
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import boot_test as boot
import phase2_candidate_vm as candidate
import phase2_vm
from phase2_native_glycin import compressed_payload
import vm

ROOT=vm.ROOT
SOURCE=ROOT/'.local/phase2/native-installer-1/installed.qcow2'
HOST_FLOOR=100*1024**3+512*1024**2
STOP_HEADROOM=1024**3
WRITE_BPS=16*1024**2
BOOT_KEYS={'boot_id','root_uuid','persistent_marker_sha256','kernel_release','installer_media_attached','fresh_owner_login','initramfs_sha256'}


def private(path,directory=False):
    info=path.lstat()
    if (path.resolve()!=path or info.st_uid!=os.getuid() or stat.S_IMODE(info.st_mode)!=(0o700 if directory else 0o600) or
            (not stat.S_ISDIR(info.st_mode) if directory else not stat.S_ISREG(info.st_mode) or info.st_nlink!=1)):
        raise ValueError('installed_private_custody')
    return path


def save(path,value):candidate.save(path,value)


def validate_handoff(value):
    if (not isinstance(value,dict) or value.get('kind')!='native-installed-disk-handoff-v1' or
            value.get('state')!='completed-install-detached-boots-pending' or value.get('version')!=1 or
            value.get('firmware') not in ('bios','uefi') or value.get('target_serial')!='TODDY-INSTALL-P2-1' or
            value.get('production_ready') is not False or value.get('detached_boots_collected')!=0 or
            not isinstance(value.get('operation_id'),str) or not re.fullmatch('[0-9a-f]{32}',value['operation_id'])):raise ValueError('installed_actual_handoff_required')
    for key in ('plan_sha256','input_manifest_sha256','image_manifest_sha256','kernel_sha256','initramfs_sha256','initramfs_source_sha256','grub_config_sha256'):
        if not isinstance(value.get(key),str) or not re.fullmatch('[a-f0-9]{64}',value[key]):raise ValueError('installed_handoff_hash')
    if not isinstance(value.get('root_uuid'),str) or not re.fullmatch('[a-fA-F0-9-]{4,40}',value['root_uuid']):raise ValueError('installed_root_uuid')
    owner=value.get('expected_owner',{})
    if not isinstance(owner,dict):raise ValueError('installed_fresh_owner')
    if (set(owner)!={'username','uid','gid'} or not isinstance(owner['username'],str) or not re.fullmatch('[a-z][a-z0-9_-]{0,31}',owner['username']) or
            owner['username'] in ('root','lfs','tester','builder','toddy','toddy-live') or
            type(owner['uid']) is not int or type(owner['gid']) is not int or not 1000<=owner['uid']<=60000 or not 1000<=owner['gid']<=60000):raise ValueError('installed_fresh_owner')
    return value


def cold_handoff(handoff_path):
    """A saved review/handoff alone never authorizes a detached installed boot."""
    private(SOURCE.parent,True);private(SOURCE);private(handoff_path)
    cold_path=private(SOURCE.parent/'cold.json');cold=json.loads(cold_path.read_bytes())
    handoff=validate_handoff(json.loads(handoff_path.read_bytes()))
    if (cold.get('version')!=1 or cold.get('kind')!='native-live-install-cold-handoff-v1' or cold.get('state')!='cold-completed-install' or
            cold.get('media_detached') is not True or cold.get('container_final_state',{}).get('Running') is not False or cold.get('container_final_state',{}).get('ExitCode')!=0 or
            cold.get('handoff_sha256')!=boot.digest(handoff_path) or cold.get('controller_sha256')!=boot.digest(Path(__file__).with_name('native_installer_live.py')) or cold.get('vault_sha256')!=boot.digest(Path(__file__).with_name('installer_credential_vault.py')) or
            cold.get('disk_identity')!=phase2_vm.backing_identity(SOURCE) or cold.get('disk_ctime_ns')!=SOURCE.stat().st_ctime_ns or cold.get('disk_sha256')!=boot.digest(SOURCE)):
        raise ValueError('installed_actual_cold_completed_handoff_required')
    sys.path.insert(0,str(ROOT))
    from runtime.installer.composition import validate_finalizer_report
    from runtime.installer.native_finalizer import payload_module
    p=payload_module();inputs=json.loads(private(SOURCE.parent/'inputs.json').read_bytes())
    if handoff.get('source_sha256')!=inputs['runtime_source_sha256'] or cold['controller_sha256']!=inputs['producer_sha256'] or cold['vault_sha256']!=inputs['vault_sha256']:raise ValueError('installed_cold_source_binding')
    if set(handoff.get('finalizer_reports_sha256',{}))!=p.CHECKS:raise ValueError('installed_nine_preserved_reports_required')
    for name in p.CHECKS:
        path=private(SOURCE.parent/'evidence'/(name+'.json'))
        if boot.digest(path)!=handoff['finalizer_reports_sha256'][name]:raise ValueError('installed_finalizer_report_changed')
        validate_finalizer_report(json.loads(path.read_bytes()),name,inputs['descriptor'])
    return handoff,cold


def payloads(handoff,number,recovery):
    probe=(Path(__file__).with_name('installed-owner-probe.py')).read_bytes()
    observer=Path(__file__).with_name('installed-auth-wait.py').read_bytes()
    source=('EXPECTED='+repr(handoff)+'\nROUND='+str(number)+'\nRECOVERY='+repr(recovery)+'\n').encode()+observer+b'\nstart_auth_wait(EXPECTED,ROUND,RECOVERY)\n'+probe
    return {'systemd.extra-unit.toddy-boot-probe.service':Path(__file__).with_name('desktop-boot-probe.service').read_bytes(),
        'systemd.unit-dropin.multi-user.target':Path(__file__).with_name('boot-probe.target.conf').read_bytes(),
        'toddy.boot-probe':compressed_payload(source)}


def qemu(handoff,number,recovery):
    args=boot.qemu_arguments(handoff['firmware'],payloads(handoff,number,recovery))
    args[args.index('-cpu')+1]='host';args[args.index('-m')+1]='4096'
    root='file=/work/target.qcow2,if=none,id=root,format=qcow2'
    args[args.index(root)]=root+',bps_wr='+str(WRITE_BPS)
    args[args.index('file:/work/serial.log')]='file:/work/serial-'+str(number)+'.log'
    old='virtio-blk-pci,drive=root,serial=TODDY-BOOT-TEST'
    args[args.index(old)]='virtio-blk-pci,drive=root,serial='+handoff['target_serial']
    return args+['-serial','file:/work/observation-'+str(number)+'.log','-vga','virtio','-device','qemu-xhci,id=usb',
        '-device','usb-tablet,bus=usb.0','-device','usb-kbd,bus=usb.0','-qmp','unix:/work/q-'+str(number)+',server=on,wait=off']


def parse_observation(raw,handoff,number,recovery):
    rows=[json.loads(line.removeprefix('TODDY_INSTALLED_OWNER ')) for line in raw.splitlines() if line.startswith('TODDY_INSTALLED_OWNER ')]
    if len(rows)!=1 or set(rows[0])!={'state','observation'} or rows[0]['state']!='observed':raise ValueError('installed_actual_observation_missing')
    row=rows[0]['observation']
    if (set(row)!=BOOT_KEYS|{'session_type','round','recovery','observer_only_extra_write'} or row['round']!=number or row['recovery'] is not recovery or
            row['session_type']!=('tty' if recovery else 'wayland') or row['root_uuid']!=handoff['root_uuid'] or
            row['kernel_release']!='7.1.8-toddy' or row['initramfs_sha256']!=handoff['initramfs_sha256'] or
            row['installer_media_attached'] is not False or row['fresh_owner_login'] is not True or
            row['observer_only_extra_write']!='explicit-owner-persistence-marker' or
            not re.fullmatch('[a-f0-9-]{36}',row['boot_id']) or row['persistent_marker_sha256']!=hashlib.sha256((handoff['plan_sha256']+'\n').encode()).hexdigest()):raise ValueError('installed_observation_mismatch')
    return row


def tool(common,image,*args):return subprocess.check_output(['docker','run','--rm',*common,image,*args],text=True)


def run(context,number,handoff_path=None):
    resource.setrlimit(resource.RLIMIT_CORE,(0,0));os.umask(0o077)
    if os.getuid()==0 or not context.is_absolute() or context.parent!=ROOT/'.local/phase2' or not re.fullmatch('installed-owner-[a-z0-9-]{1,32}',context.name):raise ValueError('installed_context')
    lock=open(vm.VM/'native-boot-test.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    boot.refuse_running_tests();phase2_vm.require_quiescent();baseline=candidate.bases()
    if subprocess.check_output(['docker','ps','-q','--filter','label=toddy.candidate=phase2-candidate'],text=True).strip():raise ValueError('installed_candidate_must_be_cold')
    if subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip():raise ValueError('installed_commit_inputs_first')
    if json.loads((ROOT/'status.json').read_bytes()).get('owner_review',{}).get('phase_2_approved') is not True:raise ValueError('installed_owner_authorization')
    import shutil
    private(SOURCE.parent,True);private(SOURCE)
    storage={'source_allocated_bytes':SOURCE.stat().st_blocks*512,'host_floor_bytes':HOST_FLOOR,'boot_extra_bytes':2*1024**3,
        'write_bytes_per_second':WRITE_BPS,'stop_headroom_bytes':STOP_HEADROOM}
    if not capacity_admitted(shutil.disk_usage(ROOT).free,storage['source_allocated_bytes']):raise ValueError('installed_host_reserve')
    public_sources={name:boot.digest(Path(__file__).with_name(name)) for name in ('installed-owner-probe.py','installed-auth-wait.py','desktop-boot-probe.service','boot-probe.target.conf','boot_test.py','phase2_native_glycin.py')}
    image=subprocess.check_output(['docker','image','inspect','--format','{{.Id}}',vm.IMAGE],text=True).strip()
    if number==1:
        if context.exists() or context.is_symlink():raise ValueError('installed_existing_context_no_replay')
        private(SOURCE.parent,True);private(SOURCE)
        handoff,cold=cold_handoff(handoff_path)
        source={'identity':phase2_vm.backing_identity(SOURCE),'sha256':cold['disk_sha256']}
        context.mkdir(mode=0o700);save(context/'handoff.json',handoff)
        save(context/'inputs.json',{'source':source,'handoff_sha256':boot.digest(context/'handoff.json'),'accepted':baseline,'producer_sha256':boot.digest(Path(__file__)),'public_sources':public_sources,'container_image':image})
    else:
        private(context,True)
        if handoff_path is not None:raise ValueError('installed_fixed_inputs_only')
        if not (context/('round-'+str(number-1)+'.json')).exists():raise ValueError('installed_prior_real_boot_required')
        if (context/('intent-'+str(number)+'.json')).exists():raise ValueError('installed_round_uncertain_no_replay')
    private(SOURCE.parent,True);private(SOURCE)
    inputs=json.loads((context/'inputs.json').read_bytes());handoff=validate_handoff(json.loads((context/'handoff.json').read_bytes()))
    if number>1:handoff,cold=cold_handoff(context/'handoff.json')
    if (inputs['accepted']!=baseline or inputs['handoff_sha256']!=boot.digest(context/'handoff.json') or
            inputs['producer_sha256']!=boot.digest(Path(__file__)) or phase2_vm.backing_identity(SOURCE)!=inputs['source']['identity'] or cold['disk_sha256']!=inputs['source']['sha256']):raise ValueError('installed_cold_inputs_changed')
    if inputs['public_sources']!=public_sources or inputs['container_image']!=image:raise ValueError('installed_observer_or_runtime_changed')
    common=['--user',f'{os.getuid()}:{os.getgid()}','--cap-drop=ALL','--security-opt=no-new-privileges','--network=none','--read-only',
        '-v',f'{SOURCE}:/installed/source.qcow2:ro','-v',f'{context}:/work']
    if number==1:
        info=json.loads(tool(common,image,'qemu-img','info','--output=json','--backing-chain','/installed/source.qcow2'))
        if len(info)!=1 or info[0]['format']!='qcow2' or info[0]['virtual-size']!=64*1024**3:raise ValueError('installed_self_contained_64g_qcow2_required')
        tool(common,image,'qemu-img','check','/installed/source.qcow2')
        tool(common,image,'qemu-img','create','-f','qcow2','-F','qcow2','-b','/installed/source.qcow2','/work/target.qcow2')
        if handoff['firmware']=='uefi':
            hashes=tool(common,image,'sha256sum',boot.CODE,boot.VARS)
            if {line.split()[1]:line.split()[0] for line in hashes.splitlines()}!=boot.FIRMWARE_HASHES:raise ValueError('installed_firmware_custody')
            tool(common,image,'cp',boot.VARS,'/work/OVMF_VARS.fd')
    if number>1:
        last=json.loads((context/('round-'+str(number-1)+'.json')).read_bytes())
        if last.get('state')!='observed' or last.get('container_final_state',{}).get('Running') is not False:raise ValueError('installed_prior_stopped_observation_required')
        if phase2_vm.backing_identity(context/'target.qcow2')!=last['overlay_identity']:raise ValueError('installed_persistent_overlay_changed')
    args=qemu(handoff,number,number==3);run_id=uuid.uuid4().hex
    command=['docker','create','--name','toddy-installed-'+run_id[:12],'--label','toddy.boot-test='+run_id,*common,
        '--device','/dev/kvm','--group-add',str(Path('/dev/kvm').stat().st_gid),'--memory','5g','--cpus','2',image,*args]
    save(context/('intent-'+str(number)+'.json'),{'round':number,'run_id':run_id,'command':command,'source':inputs['source'],'recovery':number==3,'storage':storage,'overlay_pin':{key:value for key,value in phase2_vm.backing_identity(context/'target.qcow2').items() if key in ('device','inode')},'intent_time_ns':time.time_ns()})
    cid=subprocess.check_output(command,text=True).strip();save(context/'active.json',{'container_id':cid,'run_id':run_id,'round':number})
    try:
        subprocess.run(['docker','start',cid],check=True,stdout=subprocess.DEVNULL)
        wait_owned(cid,run_id,context,number)
    finally:final=boot.stop_owned_container(cid,run_id)
    if candidate.bases()!=baseline or phase2_vm.backing_identity(SOURCE)!=inputs['source']['identity'] or boot.digest(SOURCE)!=inputs['source']['sha256']:raise ValueError('installed_backing_changed')
    if (context/('operator-stop-'+str(number)+'.json')).exists():raise ValueError('installed_operator_stop_no_boot_acceptance')
    # Log files are unique per round; QEMU file chardev truncates each boot.
    raw=(context/('observation-'+str(number)+'.log')).read_text();row=parse_observation(raw,handoff,number,number==3)
    if number>1:
        prior=json.loads((context/'round-1.json').read_bytes())['observation']
        if row['boot_id']==prior['boot_id'] or row['persistent_marker_sha256']!=prior['persistent_marker_sha256']:raise ValueError('installed_distinct_boot_persistence')
    result={'state':'observed','observation':row,'container_final_state':final,'overlay_identity':phase2_vm.backing_identity(context/'target.qcow2'),
        'observation_sha256':hashlib.sha256(raw.encode()).hexdigest(),'source_unchanged':True,'recovery_only':number==3,
        'handoff_sha256':inputs['handoff_sha256'],'observer_sha256':boot.digest(Path(__file__).with_name('installed-owner-probe.py'))}
    save(context/('round-'+str(number)+'.json'),result)
    if number==2:
        first=json.loads((context/'round-1.json').read_bytes())['observation']
        receipt={key:handoff[key] for key in ('firmware','input_manifest_sha256','image_manifest_sha256','kernel_sha256','initramfs_source_sha256')}
        receipt.update(kind='native-detached-installed-boot-v1',boots=[{key:item[key] for key in BOOT_KEYS} for item in (first,row)])
        save(context/('boot-'+handoff['firmware']+'.json'),receipt)
    print(json.dumps({'state':'actual-observation-preserved','context':str(context),'round':number,'production_ready':False}))


def capacity_admitted(free,allocated):
    return type(free) is int and type(allocated) is int and allocated>=0 and free>=HOST_FLOOR+allocated+2*1024**3


def capacity_stop_required(free):
    return free<HOST_FLOOR+STOP_HEADROOM


def powerdown_owned(cid,run_id,path):
    row=json.loads(subprocess.check_output(['docker','inspect',cid],text=True))[0]
    if row['Config']['Labels'].get('toddy.boot-test')!=run_id or not row['State']['Running']:raise ValueError('installed_owned_powerdown')
    with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as stream:
        stream.settimeout(2);stream.connect(str(path));wire=stream.makefile('rwb',buffering=0);json.loads(wire.readline())
        for name in ('qmp_capabilities','system_powerdown'):
            deadline=time.monotonic()+2
            wire.write(json.dumps({'execute':name}).encode()+b'\n')
            while True:
                if time.monotonic()>deadline:raise TimeoutError('installed_powerdown_deadline')
                result=json.loads(wire.readline())
                if 'error' in result:raise ValueError('installed_powerdown_failed')
                if 'return' in result:break


def wait_owned(cid,run_id,context,number):
    import shutil
    deadline=time.monotonic()+960
    process=subprocess.Popen(['docker','wait',cid],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    try:
        while process.poll() is None:
            free=shutil.disk_usage(ROOT).free
            if capacity_stop_required(free):
                save(context/('capacity-stop-'+str(number)+'.json'),{'state':'capacity-stop-intended','free_bytes':free,
                    'floor_bytes':HOST_FLOOR,'stop_headroom_bytes':STOP_HEADROOM,'write_bytes_per_second':WRITE_BPS,
                    'round':number,'boot_accepted':False})
                try:powerdown_owned(cid,run_id,context/('q-'+str(number)))
                except (OSError,ValueError):pass
                # Outer finally always stops/rechecks this exact owned container.
                try:process.wait(timeout=5)
                except subprocess.TimeoutExpired:pass
                raise ValueError('installed_capacity_stop_uncertain_inspect_no_replay')
            if time.monotonic()>deadline:raise TimeoutError('installed_boot_timeout')
            time.sleep(.5)
        stdout,stderr=process.communicate(timeout=2)
        if process.returncode or stdout.strip()!='0':raise ValueError('installed_native_exit')
        if capacity_stop_required(shutil.disk_usage(ROOT).free):raise ValueError('installed_postboot_capacity_not_accepted')
    finally:
        if process.poll() is None:process.terminate()
        process.communicate(timeout=5)


def key_codes(char):
    if char in 'abcdefghijklmnopqrstuvwxyz0123456789':return [char]
    if char in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':return ['shift',char.lower()]
    plain={'-':'minus','_':None,' ':'spc','.':'dot','/':'slash','=':'equal'}
    if char=='_':return ['shift','minus']
    if char in plain:return [plain[char]]
    raise ValueError('installed_private_input_keyboard_character_unsupported')


def qmp(context,action):
    import shutil
    private(context,True);active=json.loads((context/'active.json').read_bytes())
    inspect=json.loads(subprocess.check_output(['docker','inspect',active['container_id']],text=True))[0]
    handoff=validate_handoff(json.loads((context/'handoff.json').read_bytes()))
    mounts={(row['Source'],row['Destination'],row['RW']) for row in inspect['Mounts'] if row['Type']=='bind'}
    if (inspect['Config']['Labels'].get('toddy.boot-test')!=active['run_id'] or not inspect['State']['Running'] or
            inspect['Config']['Cmd']!=qemu(handoff,active['round'],active['round']==3) or
            mounts!={(str(SOURCE),'/installed/source.qcow2',False),(str(context),'/work',True)} or
            inspect['HostConfig']['NetworkMode']!='none'):
        raise ValueError('installed_owned_running_vm_required')
    if action=='stop':
        save(context/('operator-stop-'+str(active['round'])+'.json'),{'state':'stop-intended','round':active['round'],'boot_accepted':False})
        try:powerdown_owned(active['container_id'],active['run_id'],context/('q-'+str(active['round'])))
        except (OSError,ValueError):pass
        try:subprocess.run(['docker','wait',active['container_id']],capture_output=True,timeout=5,check=True)
        except (subprocess.TimeoutExpired,subprocess.CalledProcessError):pass
        final=boot.stop_owned_container(active['container_id'],active['run_id'])
        return {'stopped':not final['Running'],'boot_accepted':False}
    if capacity_stop_required(shutil.disk_usage(ROOT).free):
        powerdown_owned(active['container_id'],active['run_id'],context/('q-'+str(active['round'])))
        raise ValueError('installed_control_capacity_stop_no_input')
    with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as stream:
        stream.settimeout(10);stream.connect(str(context/('q-'+str(active['round']))));wire=stream.makefile('rwb',buffering=0);json.loads(wire.readline())
        def call(name,arguments=None):
            wire.write(json.dumps({'execute':name,**({'arguments':arguments} if arguments else {})}).encode()+b'\n')
            while True:
                result=json.loads(wire.readline())
                if 'error' in result:raise ValueError('installed_qmp_command_failed')
                if 'return' in result:return result['return']
        call('qmp_capabilities')
        if action=='capture':
            name='frame-'+uuid.uuid4().hex+'.ppm';call('screendump',{'filename':'/work/'+name})
            save(context/('input-frame-'+str(active['round'])+'.json'),{'frame':name,'sha256':boot.digest(context/name),'round':active['round']})
            return {'frame':str(context/name)}
        if action in ('username','password'):
            frame=json.loads((context/('input-frame-'+str(active['round'])+'.json')).read_bytes())
            if frame['sha256']!=boot.digest(context/frame['frame']):raise ValueError('installed_inspect_actual_frame_first')
            value=json.loads((context/'handoff.json').read_bytes())['expected_owner']['username'] if action=='username' else getpass.getpass('Actual installed owner password (RAM only): ')
            if not 1<=len(value)<=128:raise ValueError('installed_private_input_length')
            codes=[key_codes(char) for char in value]
            import time
            for item in codes:call('send-key',{'keys':[{'type':'qcode','data':code} for code in item],'hold-time':60});time.sleep(.1)
            value=None;codes=None
        else:
            codes={'enter':['ret'],'down':['down'],'up':['up'],'escape':['esc'],'tab':['tab'],'tty':['ctrl','alt','f2']}[action]
            call('send-key',{'keys':[{'type':'qcode','data':code} for code in codes],'hold-time':80})
        return {'input_sent':action,'login_observed':False}


def main():
    resource.setrlimit(resource.RLIMIT_CORE,(0,0));os.umask(0o077)
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('action',choices=['run','stop','capture','username','password','enter','down','up','escape','tab','tty'])
    parser.add_argument('--context',required=True,type=Path);parser.add_argument('--round',type=int,choices=(1,2,3));parser.add_argument('--handoff',type=Path)
    args=parser.parse_args()
    if args.action=='run':
        if args.round is None or (args.round==1 and args.handoff is None):parser.error('run requires round and first round requires handoff')
        run(args.context,args.round,args.handoff)
    else:print(json.dumps(qmp(args.context,args.action)))

if __name__=='__main__':main()

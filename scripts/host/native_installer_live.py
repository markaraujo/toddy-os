#!/usr/bin/env python3
"""First real live-ISO blank-disk qualification controller; no automatic replay."""
import argparse,base64,fcntl,getpass,hashlib,json,os,re,resource,secrets,select,shutil,socket,stat,subprocess,sys,time,uuid
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE),str(HERE.parents[1]),str(HERE.parents[1]/'scripts/build/phase2')]
import vm,boot_test as boot,phase2_vm,phase2_candidate_vm as candidate
import installed_owner_boot as installed
from phase2_native_glycin import compressed_payload
import installer_input_snapshot as snapshot
import installer_credential_vault as vault_module
credential_vault=vault_module.serve
from runtime.installer.disk_plan import validate_plan,OPTION_FIELDS
from runtime.installer.composition import validate_finalizer_report
import offline_payload as payload

ROOT=vm.ROOT;CONTEXT=ROOT/'.local/phase2/native-installer-1';WORK=CONTEXT/'run';SERIAL='TODDY-INSTALL-P2-1'
HOST_FLOOR=100*1024**3+512*1024**2;HEADROOM=1024**3;WRITE_BPS=16*1024**2
MVP=False
def configure(mvp=False):
    global MVP,CONTEXT,WORK
    snapshot.configure(mvp);MVP=mvp;CONTEXT=snapshot.CONTEXT;WORK=CONTEXT/'run'
    if mvp:installed.configure_mvp()

ACTIONS={'review','execute','cancel','status','gui','collect','finish','capture'}
SERVICE=b'''[Unit]
Description=Disposable live installer root qualification controller
ConditionPathExists=!/etc/initrd-release
After=local-fs.target
[Service]
Type=exec
Environment=PATH=/usr/bin:/usr/sbin LC_ALL=C.UTF-8 PYTHONDONTWRITEBYTECODE=1
PrivateMounts=yes
LoadCredential=toddy.boot-probe
ExecStart=/usr/bin/python3 %d/toddy.boot-probe
RuntimeMaxSec=7200
KillMode=mixed
TimeoutStopSec=1900
StandardOutput=journal+console
StandardError=journal+console
'''


def save(path,value):candidate.save(path,value);path.chmod(0o600)
def private(path,directory=False):return installed.private(path,directory)
def read(path):
    path=private(path)
    if path.stat().st_size>16*1024**2:raise ValueError('installer_control_metadata_bound')
    return json.loads(path.read_bytes())


def review_valid(value,options,descriptor):
    if not isinstance(value,dict) or set(value)!={'state','disk_writes','plan'} or value['state']!='qualification-review-only' or value['disk_writes'] is not False:raise ValueError('actual_native_review_required')
    plan=validate_plan(value['plan']);disk=plan['target']
    if disk['serial']!=SERIAL or disk['size']!=64*1024**3 or not disk['virtual'] or not disk['blank'] or disk['readonly'] or disk['mounted'] or plan['options']!=options or plan['payload']['sha256']!=descriptor['payload_manifest_sha256']:raise ValueError('exact_blank_serial_options_payload_required')
    return plan


def admission(free,storage):
    bound=storage.get('root_storage_bound_bytes')
    if type(bound) is not int or bound<=0:raise ValueError('actual_payload_storage_bound_required')
    return free>=HOST_FLOOR+2*bound+4*1024**3


def qemu(firmware,snapshot_sha):
    source=('EXPECTED_SNAPSHOT_SHA256='+repr(snapshot_sha)+'\nQUALIFICATION_PROFILE='+repr(snapshot.MVP_CLASS if MVP else 'standard')+'\n').encode()+(HERE/'installer-live-probe.py').read_bytes()
    args=boot.qemu_arguments(firmware,{'systemd.extra-unit.toddy-boot-probe.service':SERVICE,
        'systemd.unit-dropin.multi-user.target':b'[Unit]\nWants=toddy-boot-probe.service\n','toddy.boot-probe':compressed_payload(source)})
    args[args.index('-cpu')+1]='host';args[args.index('-m')+1]='8192';args[args.index('-smp')+1]='4'
    args[args.index('strict=on')]='order=d,strict=on'
    args[args.index('file=/work/target.qcow2,if=none,id=root,format=qcow2')]='file=/installed/installed.qcow2,if=none,id=root,format=qcow2,bps_wr='+str(WRITE_BPS)
    args[args.index('virtio-blk-pci,drive=root,serial=TODDY-BOOT-TEST')]='virtio-blk-pci,drive=root,serial='+SERIAL
    return args+['-drive','file=/live/live.iso,format=raw,media=cdrom,readonly=on',
        '-drive','file=/inputs/inputs.iso,if=none,id=inputs,format=raw,readonly=on',
        '-device','virtio-blk-pci,drive=inputs,serial=TODDY-INSTALL-DATA',
        '-device','virtio-serial-pci','-chardev','socket,id=auth,path=/work/auth,server=on,wait=off',
        '-device','virtserialport,chardev=auth,name=io.toddy.installer.control',
        '-vga','virtio','-device','qemu-xhci,id=usb','-device','usb-tablet,bus=usb.0','-device','usb-kbd,bus=usb.0',
        '-qmp','unix:/work/q,server=on,wait=off']


def mounts(iso):
    return {(str(iso),'/live/live.iso',False),(str(CONTEXT/'qualification-inputs/inputs.iso'),'/inputs/inputs.iso',False),
        (str(CONTEXT/'installed.qcow2'),'/installed/installed.qcow2',True),(str(WORK),'/work',True)}


def owned(active,inputs):
    row=json.loads(subprocess.check_output(['docker','inspect',active['container_id']],text=True))[0]
    actual={(item['Source'],item['Destination'],item['RW']) for item in row['Mounts'] if item['Type']=='bind'}
    if row['Config']['Labels'].get('toddy.boot-test')!=active['run_id'] or row['Config']['Cmd']!=qemu(inputs['firmware'],inputs['snapshot_sha256']) or actual!=mounts(Path(inputs['iso'])) or row['HostConfig']['NetworkMode']!='none' or not row['State']['Running']:raise ValueError('exact_owned_live_controller_required')
    return row


def tool(common,image,*args):return subprocess.check_output(['docker','run','--rm',*common,image,*args],text=True)


def evidence(result,inputs,options):
    if result.get('state')!='actual-evidence-collected' or not isinstance(result.get('files'),dict) or len(result['files'])!=10:raise ValueError('actual_ten_installer_artifacts_required')
    expected={'installed-handoff-'+options['operation_id']+'.json'}|{name+'.json' for name in payload.CHECKS}
    if set(result['files'])!=expected:raise ValueError('actual_nine_reports_and_handoff_required')
    decoded={name:base64.b64decode(data,validate=True) for name,data in result['files'].items()}
    if sum(map(len,decoded.values()))>8*1024**2:raise ValueError('native_evidence_bound')
    handoff=installed.validate_handoff(json.loads(decoded['installed-handoff-'+options['operation_id']+'.json']))
    plan=review_valid(read(CONTEXT/'review.json'),options,inputs['descriptor'])
    if handoff['plan_sha256']!=plan['plan_sha256'] or handoff['operation_id']!=options['operation_id'] or handoff['firmware']!=inputs['firmware']:raise ValueError('actual_handoff_plan_binding')
    if handoff.get('expected_owner')!={key:options[key] for key in ('username','uid','gid')} or handoff.get('input_manifest_sha256')!=inputs['descriptor']['payload_manifest_sha256'] or handoff.get('image_manifest_sha256')!=inputs['descriptor']['image_manifest_sha256'] or handoff.get('source_sha256')!=inputs['runtime_source_sha256'] or handoff.get('kernel_sha256')!=inputs['expected_kernel_sha256'] or handoff.get('payload_storage')!=inputs['payload_storage']:raise ValueError('actual_handoff_frozen_input_source_owner_binding')
    for name in payload.CHECKS:
        raw=decoded[name+'.json'];validate_finalizer_report(json.loads(raw),name,inputs['descriptor'])
        if hashlib.sha256(raw).hexdigest()!=handoff['finalizer_reports_sha256'][name]:raise ValueError('actual_finalizer_report_custody')
    if shutil.disk_usage(CONTEXT).free<HOST_FLOOR+sum(map(len,decoded.values()))+16*1024**2:raise ValueError('actual_host_evidence_capacity_required')
    target=CONTEXT/'evidence'
    if target.exists():raise ValueError('preserve_prior_collect_no_replay')
    target.mkdir(mode=0o700)
    for name,raw in decoded.items():
        with (target/name).open('xb') as stream:os.fchmod(stream.fileno(),0o600);stream.write(raw);stream.flush();os.fsync(stream.fileno())
    save(CONTEXT/'handoff.json',handoff)
    return {'state':'actual-nine-reports-preserved','handoff':str(CONTEXT/'handoff.json'),'production_ready':False}


def control_request(request,inputs,options,events):
    if not isinstance(request,dict) or set(request)-{'action','request_id','confirm','password','generated'} or request.get('action') not in ACTIONS or not isinstance(request.get('request_id'),str) or not re.fullmatch('[a-z0-9-]{1,64}',request['request_id']):raise ValueError('fixed_owned_controller_action')
    action=request['action'];seen={row['request_id'] for row in events if 'request_id' in row}
    if request['request_id'] in seen:raise ValueError('inspect_prior_request_no_replay')
    if action=='execute':
        plan=review_valid(read(CONTEXT/'review.json'),options,inputs['descriptor'])
        if request.get('confirm')!=plan['plan_sha256'] or any(row.get('action')=='execute' for row in events):raise ValueError('explicit_reviewed_hash_or_uncertain_execute_no_replay')
        if request.get('generated') is not True and (not isinstance(request.get('password'),str) or not 12<=len(request['password'].encode())<=1024):raise ValueError('private_owner_password_required')
        if 'generated' in request and request['generated'] is not True:raise ValueError('explicit_generated_qualification_credential_only')
        if request.get('generated') and 'password' in request:raise ValueError('one_private_credential_mode_only')
    elif 'password' in request or 'confirm' in request or 'generated' in request:raise ValueError('private_input_only_for_exact_execute')
    if action=='review':
        if any(row.get('action')=='review' for row in events):raise ValueError('inspect_existing_review_no_replay')
        request=dict(request,options=options)
    if action=='finish':
        executions=[row for row in events if row.get('guest',{}).get('event')=='execute-ended']
        if any(row.get('action')=='execute' for row in events) and not executions:raise ValueError('actual_terminal_result_required_before_finish')
        if executions and executions[-1]['guest'].get('result',{}).get('state')=='completed' and not (CONTEXT/'handoff.json').exists():raise ValueError('collect_nine_reports_before_completed_finish')
    return request


def run(iso,iso_sha,options_path):
    if os.getuid()==0 or CONTEXT.resolve()!=CONTEXT:raise ValueError('nonroot_owned_installer_controller_required')
    resource.setrlimit(resource.RLIMIT_CORE,(0,0));os.umask(0o077)
    lock=open(vm.VM/'native-boot-test.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    boot.refuse_running_tests();phase2_vm.require_quiescent();baseline=candidate.bases()
    if subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip():raise ValueError('commit_reviewed_controller_inputs_first')
    if json.loads((ROOT/'status.json').read_bytes()).get('owner_review',{}).get('phase_2_approved') is not True:raise ValueError('owner_phase2_authorization_required')
    private(CONTEXT,True)
    if {path.name for path in CONTEXT.iterdir()}!={'qualification-inputs'}:raise ValueError('existing_or_uncertain_context_no_restart')
    folder=CONTEXT/'qualification-inputs';private(folder,True);complete=read(folder/'complete.json');description=read(folder/'snapshot.json')
    if complete.get('state')!='qualification-snapshot-created-not-booted' or complete['snapshot_sha256']!=boot.digest(folder/'snapshot.json') or complete['iso_sha256']!=boot.digest(private(folder/'inputs.iso')):raise ValueError('actual_reviewed_auxiliary_iso_required')
    if (MVP and (description.get('delivery_class')!=snapshot.MVP_CLASS or description.get('g2_eligible') is not False)) or (not MVP and 'delivery_class' in description):raise ValueError('matching_explicit_installer_delivery_profile_required')
    iso=snapshot.regular(iso)
    if not re.fullmatch('[a-f0-9]{64}',iso_sha) or boot.digest(iso)!=iso_sha:raise ValueError('actual_live_iso_hash_required')
    with iso.open('rb') as stream:
        stream.seek(32769)
        if stream.read(5)!=b'CD001':raise ValueError('actual_live_iso9660_required')
    options=json.loads(snapshot.regular(options_path).read_bytes())
    if not isinstance(options,dict) or set(options)!=OPTION_FIELDS or options['boot_mode'] not in ('bios','uefi'):raise ValueError('nonsecret_exact_installer_options_required')
    if MVP and options['boot_mode']!='uefi':raise ValueError('fixed_MVP_UEFI_first_install_required')
    if not isinstance(options['extras'],list) or any(not isinstance(value,str) or value not in ('docker','opencode','vscode') for value in options['extras']):raise ValueError('typed_nonsecret_optional_intent_required')
    options['extras']=sorted(options['extras'])
    if not admission(shutil.disk_usage(ROOT).free,description.get('payload_storage',{})):raise ValueError('host_reserve_plus_actual_install_storage_required')
    if description['files'].get('source/scripts/host/installer-live-probe.py')!=boot.digest(HERE/'installer-live-probe.py'):raise ValueError('reviewed_probe_snapshot_differs')
    WORK.mkdir(mode=0o700);save(CONTEXT/'options.json',options)
    image=subprocess.check_output(['docker','image','inspect','--format','{{.Id}}',vm.IMAGE],text=True).strip()
    inputs={'iso':str(iso),'iso_sha256':iso_sha,'firmware':options['boot_mode'],'snapshot_sha256':complete['snapshot_sha256'],
        'auxiliary_iso_sha256':complete['iso_sha256'],'descriptor':description['descriptor'],'runtime_source_sha256':description['runtime_source_sha256'],
        'expected_kernel_sha256':description['expected_kernel_sha256'],'payload_storage':description['payload_storage'],'accepted':baseline,'container_image':image,
        'producer_sha256':boot.digest(Path(__file__)),'vault_sha256':boot.digest(Path(vault_module.__file__)),'probe_sha256':boot.digest(HERE/'installer-live-probe.py')}
    if MVP:inputs.update(delivery_class=snapshot.MVP_CLASS,qualification_profile=snapshot.MVP_CLASS,g2_eligible=False)
    save(CONTEXT/'inputs.json',inputs);run_id=uuid.uuid4().hex
    common=['--user',str(os.getuid())+':'+str(os.getgid()),'--cap-drop=ALL','--security-opt=no-new-privileges','--network=none','--read-only',
        '-v',str(WORK)+':/work']
    save(CONTEXT/'create-intent.json',{'state':'new-64g-image-intended','run_id':run_id,'serial':SERIAL,'backing':None,'guest_started':False})
    tool(common,image,'qemu-img','create','-f','qcow2','/work/new.qcow2','64G');os.rename(WORK/'new.qcow2',CONTEXT/'installed.qcow2');(CONTEXT/'installed.qcow2').chmod(0o600)
    common=['--user',str(os.getuid())+':'+str(os.getgid()),'--cap-drop=ALL','--security-opt=no-new-privileges','--network=none','--read-only']
    for source,destination,writable in sorted(mounts(iso)):common+=['-v',source+':'+destination+('' if writable else ':ro')]
    info=json.loads(tool(common,image,'qemu-img','info','--output=json','--backing-chain','/installed/installed.qcow2'))
    if len(info)!=1 or info[0]['format']!='qcow2' or info[0]['virtual-size']!=64*1024**3:raise ValueError('new_self_contained_64g_required')
    if inputs['firmware']=='uefi':
        hashes=tool(common,image,'sha256sum',boot.CODE,boot.VARS)
        if {line.split()[1]:line.split()[0] for line in hashes.splitlines()}!=boot.FIRMWARE_HASHES:raise ValueError('firmware_custody')
        tool(common,image,'cp',boot.VARS,'/work/OVMF_VARS.fd')
    cid=subprocess.check_output(['docker','run','-d','--name','toddy-installer-'+run_id[:12],'--label','toddy.boot-test='+run_id,
        '--device','/dev/kvm','--group-add',str(Path('/dev/kvm').stat().st_gid),'--memory','10g','--cpus','4',*common,image,*qemu(inputs['firmware'],inputs['snapshot_sha256'])],text=True).strip()
    active={'container_id':cid,'run_id':run_id};save(CONTEXT/'active.json',active)
    events=[];pending={};server=None;guest=None;buffer=b'';finished=False;capacity_stop=False;guest_ready=False;stop_deadline=None;owner_password=None
    def persist():save(CONTEXT/'control-state.json',{'events':events})
    try:
        deadline=time.monotonic()+300
        while not (WORK/'auth').exists():
            if time.monotonic()>deadline:raise TimeoutError('guest_private_channel_timeout')
            time.sleep(.1)
        guest=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);guest.settimeout(300);guest.connect(str(WORK/'auth'))
        server=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);server.bind(str(WORK/'operator'));os.chmod(WORK/'operator',0o600);server.listen(2)
        while time.monotonic()<deadline+7200:
            if shutil.disk_usage(ROOT).free<HOST_FLOOR+HEADROOM and not capacity_stop:
                capacity_stop=True;stop_deadline=time.monotonic()+45;events.append({'state':'capacity-stop-requested','installation_accepted':False});persist()
                guest.sendall(json.dumps({'request_id':'capacity-'+uuid.uuid4().hex,'action':'cancel'}).encode()+b'\n')
            if stop_deadline is not None and time.monotonic()>stop_deadline:raise ValueError('capacity_stop_uncertain_no_replay')
            state=json.loads(subprocess.check_output(['docker','inspect',cid],text=True))[0]['State']
            if not state['Running']:break
            ready,_,_=select.select([guest,server],[],[],.5)
            if server in ready:
                client,_=server.accept();client.settimeout(5)
                try:
                    peer=client.getsockopt(socket.SOL_SOCKET,socket.SO_PEERCRED,12)
                    if int.from_bytes(peer[4:8],sys.byteorder)!=os.getuid():raise ValueError('same_owner_required')
                    request=json.loads(client.recv(8192));owned(active,inputs)
                    request=control_request(request,inputs,options,events)
                    if not guest_ready and request['action']!='capture':raise ValueError('actual_live_owner_ready_pending')
                    if capacity_stop and request['action'] not in ('status','cancel','finish','capture'):raise ValueError('capacity_stop_blocks_new_work')
                    if len(pending)>=3 or pending and request['action'] not in ('cancel','status','capture'):raise ValueError('controller_request_pending_inspect_status')
                    identity=request['request_id'];action=request['action']
                    events.append({'request_id':identity,'action':action,'state':'transport-intended'});persist()
                    if action=='capture':
                        frame='frame-'+identity+'.ppm'
                        qmp_capture(WORK/'q','/work/'+frame)
                        events.append({'request_id':identity,'result':{'frame':frame,'sha256':boot.digest(WORK/frame)}});persist();client.sendall(json.dumps(events[-1]['result']).encode());client.close()
                    else:
                        if action=='execute' and request.pop('generated',False):
                            owner_password=''.join(secrets.choice('abcdefghijklmnopqrstuvwxyz') for _ in range(24));request['password']=owner_password
                        pending[identity]=(client,action);guest.sendall(json.dumps(request,separators=(',',':')).encode()+b'\n');request=None
                except Exception as error:
                    client.sendall(json.dumps({'error':str(error) if isinstance(error,ValueError) else type(error).__name__,'write_outcome':'inspect-existing-state'}).encode());client.close()
            if guest in ready:
                data=guest.recv(65536)
                if not data:raise ValueError('guest_channel_lost_no_replay')
                buffer+=data
                if len(buffer)>12*1024**2:raise ValueError('guest_evidence_transport_bound')
                while b'\n' in buffer:
                    line,buffer=buffer.split(b'\n',1);message=json.loads(line)
                    identity=message.get('request_id')
                    if identity in pending:
                        client,action=pending.pop(identity);result=message['result']
                        if action=='review':review_valid(result,options,inputs['descriptor']);save(CONTEXT/'review.json',result)
                        if action=='collect':result=evidence(result,inputs,options)
                        if action=='finish':finished=True
                        events.append({'request_id':identity,'action':action,'result':result});persist()
                        try:client.sendall(json.dumps(result).encode())
                        except (BrokenPipeError,ConnectionResetError):pass
                        client.close()
                    else:
                        if message.get('state')=='live-root-qualification-ready':
                            if message.get('snapshot_sha256')!=inputs['snapshot_sha256'] or message.get('live_owner')!='toddy-live' or message.get('root_autologin') is not False or not re.fullmatch('[a-f0-9-]{36}',message.get('boot_id','')):raise ValueError('guest_snapshot_live_owner_binding')
                            guest_ready=True
                        if message.get('event')=='actual-journal-snapshot':
                            data=base64.b64decode(message['database_b64'],validate=True)
                            if len(data)>1024**2 or hashlib.sha256(data).hexdigest()!=message['sha256']:raise ValueError('actual_journal_snapshot_custody')
                            directory=CONTEXT/'journals';directory.mkdir(mode=0o700,exist_ok=True);path=directory/(message['sha256']+'.sqlite')
                            if not path.exists():
                                with path.open('xb') as stream:os.fchmod(stream.fileno(),0o600);stream.write(data);stream.flush();os.fsync(stream.fileno())
                            if boot.digest(path)!=message['sha256']:raise ValueError('preserved_journal_bytes_differ')
                            message={'event':'actual-journal-snapshot','sha256':message['sha256'],'path':str(path)}
                        events.append({'guest':message});persist()
        else:raise TimeoutError('owned_live_qualification_deadline')
    finally:
        for client,_ in pending.values():client.close()
        if guest is not None:guest.close()
        if server is not None:server.close()
        save(CONTEXT/'owned-stop.json',{'state':'owned-qemu-stop-intended','poweroff_acknowledged':finished,'capacity_emergency':capacity_stop,
            'normal_terminal_observed':any(row.get('guest',{}).get('event')=='execute-ended' for row in events),
            'write_outcome':'inspect-canonical-journal; emergency stop may interrupt native phase','installation_accepted':False})
        final=boot.stop_owned_container(cid,run_id)
        save(CONTEXT/'owned-stop.json',{'state':'owned-qemu-stopped','poweroff_acknowledged':finished,'capacity_emergency':capacity_stop,
            'container_final_state':final,'write_outcome':'inspect-canonical-journal; no rollback or safe-boundary inference','installation_accepted':False})
    if final['ExitCode']!=0 or not finished or capacity_stop:raise ValueError('cold_install_not_accepted_inspect_actual_state')
    if boot.digest(Path(vault_module.__file__))!=inputs['vault_sha256'] or boot.digest(Path(__file__))!=inputs['producer_sha256'] or boot.digest(HERE/'installer-live-probe.py')!=inputs['probe_sha256']:raise ValueError('reviewed_controller_source_changed')
    if candidate.bases()!=baseline or boot.digest(iso)!=inputs['iso_sha256'] or boot.digest(folder/'inputs.iso')!=inputs['auxiliary_iso_sha256']:raise ValueError('protected_inputs_changed')
    tool(common,image,'qemu-img','check','/installed/installed.qcow2')
    info=json.loads(tool(common,image,'qemu-img','info','--output=json','--backing-chain','/installed/installed.qcow2'))
    if len(info)!=1 or info[0]['format']!='qcow2' or info[0]['virtual-size']!=64*1024**3:raise ValueError('cold_self_contained_64g_required')
    handoff=read(CONTEXT/'handoff.json') if (CONTEXT/'handoff.json').exists() else None
    save(CONTEXT/'cold.json',{**({'qualification_profile':snapshot.MVP_CLASS,'g2_eligible':False} if MVP else {}),'version':1,'kind':'native-live-install-cold-handoff-v1','controller_sha256':inputs['producer_sha256'],'vault_sha256':inputs['vault_sha256'],'state':'cold-completed-install' if handoff else 'cold-without-install-acceptance','container_final_state':final,
        'disk_sha256':boot.digest(private(CONTEXT/'installed.qcow2')),'disk_identity':phase2_vm.backing_identity(CONTEXT/'installed.qcow2'),'disk_ctime_ns':(CONTEXT/'installed.qcow2').stat().st_ctime_ns,
        'media_detached':True,'generated_credential_available_in_controller_RAM':owner_password is not None,'handoff_sha256':boot.digest(CONTEXT/'handoff.json') if handoff else None,'production_ready':False})
    fcntl.flock(lock,fcntl.LOCK_UN);lock.close()
    if owner_password is not None and handoff is not None:credential_vault(owner_password,handoff,CONTEXT,save)
    owner_password=None


def qmp_capture(path,filename):
    with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as stream:
        stream.settimeout(5);stream.connect(str(path));wire=stream.makefile('rwb',buffering=0);json.loads(wire.readline())
        for command in ({'execute':'qmp_capabilities'},{'execute':'screendump','arguments':{'filename':filename}}):
            wire.write(json.dumps(command).encode()+b'\n')
            while True:
                result=json.loads(wire.readline())
                if 'error' in result:raise ValueError('actual_frame_capture_failed')
                if 'return' in result:break


def send(action,identity,confirm=None,generated=False):
    resource.setrlimit(resource.RLIMIT_CORE,(0,0));os.umask(0o077);private(CONTEXT,True)
    active=read(CONTEXT/'active.json');inputs=read(CONTEXT/'inputs.json');owned(active,inputs)
    request={'action':action,'request_id':identity}
    if action=='execute':
        plan=review_valid(read(CONTEXT/'review.json'),read(CONTEXT/'options.json'),inputs['descriptor'])
        if confirm!=plan['plan_sha256']:raise ValueError('explicit_actual_review_hash_required_before_private_input')
        request['confirm']=confirm
        if generated:request['generated']=True
        else:
            password=getpass.getpass('New installed owner password (RAM/private channel only): ')
            if password!=getpass.getpass('Repeat new installed owner password: '):raise ValueError('private_password_mismatch')
            request['password']=password
    with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as stream:
        stream.settimeout(180);stream.connect(str(WORK/'operator'));stream.sendall(json.dumps(request).encode());request=None;password=None
        raw=stream.recv(65536)
    print(raw.decode())


def main():
    parser=argparse.ArgumentParser(description=__doc__,allow_abbrev=False);parser.add_argument('--mvp',action='store_true');sub=parser.add_subparsers(dest='action',required=True)
    start=sub.add_parser('run');start.add_argument('--iso',required=True,type=Path);start.add_argument('--iso-sha256',required=True);start.add_argument('--options',required=True,type=Path)
    control=sub.add_parser('send');control.add_argument('command',choices=sorted(ACTIONS));control.add_argument('--request-id',required=True);control.add_argument('--confirm');control.add_argument('--generated-password',action='store_true')
    sub.add_parser('close-generated-credential')
    vault=sub.add_parser('type-generated-password');vault.add_argument('--installed-context',required=True,type=Path);vault.add_argument('--frame-sha256',required=True)
    args=parser.parse_args();configure(args.mvp)
    if args.action in ('type-generated-password','close-generated-credential'):
        private(CONTEXT,True)
        with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as stream:
            stream.settimeout(180)
            try:stream.connect(str(CONTEXT/'credential-vault'))
            except (FileNotFoundError,ConnectionRefusedError):raise ValueError('fixture_credential_unavailable_no_silent_reset') from None
            request={'action':'close'} if args.action=='close-generated-credential' else {'action':'type','context':str(args.installed_context),'frame_sha256':args.frame_sha256}
            stream.sendall(json.dumps(request).encode());print(stream.recv(65536).decode())
    elif args.action=='run':run(args.iso,args.iso_sha256,args.options)
    else:send(args.command,args.request_id,args.confirm,args.generated_password)


if __name__=='__main__':main()

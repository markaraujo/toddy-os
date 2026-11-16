#!/usr/bin/env python3
"""One cold native assistant GUI session; explicit local control, no replay.

run starts a fresh overlay only. send targets that exact owned context; inspect
actual phase/frame/postcondition evidence before advancing. Never auto-types a
password or marks a native phase from a host-side QMP success alone.
"""
import argparse,base64,fcntl,hashlib,importlib.util,json,os,resource,secrets,socket,subprocess,sys,threading,time,uuid,zlib
from pathlib import Path

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('native_assistant_hook',HERE/'phase2-native-assistant-hook.py')
hook=importlib.util.module_from_spec(spec);spec.loader.exec_module(hook)


def atomic(path,value):
    part=path.with_suffix('.part')
    with part.open('x') as stream:json.dump(value,stream,indent=2);stream.write('\n');stream.flush();os.fsync(stream.fileno())
    os.replace(part,path)


def packet(manifest,source):
    raw=json.dumps({'manifest':hook.validate_manifest(manifest),'hook':source},sort_keys=True).encode()
    if len(raw)>32*1024**2:raise ValueError('assistant_packet_expanded_limit')
    packed=zlib.compress(raw,9)
    if len(packed)>16*1024**2:raise ValueError('assistant_packet_limit')
    value=b'TODDY_ASSISTANT_V1\0'+len(packed).to_bytes(8,'big')+hashlib.sha256(packed).digest()+packed
    return value+b'\0'*((-len(value))%512)


def starter(expected):
    # This tiny credential-pinned loader is the only firmware code. The larger
    # exact reviewed hook/data packet is read-only, and no JSON field names an
    # executable/path/hook to fetch from a runtime source.
    return ('''import hashlib,json,zlib
from pathlib import Path
with Path('/dev/disk/by-id/virtio-TODDY-ASST-DATA').open('rb',buffering=0) as stream:
 assert stream.read(19)==b'TODDY_ASSISTANT_V1\\0'
 size=int.from_bytes(stream.read(8),'big');digest=stream.read(32)
 assert 0<size<=16*1024**2
 packed=stream.read(size)
assert hashlib.sha256(packed).hexdigest()=='''+repr(expected)+''' and hashlib.sha256(packed).digest()==digest
parser=zlib.decompressobj();raw=parser.decompress(packed,32*1024**2+1)
assert len(raw)<=32*1024**2 and parser.eof and not parser.unused_data
value=json.loads(raw)
assert set(value)=={'manifest','hook'}
exec(compile(value['hook'],'native-assistant-reviewed-hook','exec'),{'__name__':'__main__'})
''').encode()


def key_codes(char):
    if char in 'abcdefghijklmnopqrstuvwxyz0123456789':return [char]
    if char in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':return ['shift',char.lower()]
    if char in {'-',' ','.','/','='}:return [{'-':'minus',' ':'spc','.':'dot','/':'slash','=':'equal'}[char]]
    raise ValueError('assistant_input_character')


def phase_eligible(phase,status):
    story=('B11' if phase=='branding' else 'B07' if phase=='memory' else 'B08' if phase in ('grant','automation','automation-alert','automation-interrupt','revoke') else 'B10' if phase in ('integrations','integrations-bootstrap') else 'B09' if phase.startswith('voice-') else 'B06')
    rows={row['id']:row for row in status.get('milestones',[])}
    selected=rows.get(story)
    return (status.get('owner_review',{}).get('phase_2_approved') is True and selected is not None
        and all(rows.get(dependency,{}).get('status')=='completed' for dependency in selected.get('depends_on',[])))


def phase_request_error(phases,events,phase):
    """A transport ACK is pending until the guest returns its actual phase result."""
    requested=[row['result']['phase_requested'] for row in events if 'phase_requested' in row.get('result',{})]
    results=[row['native_result'] for row in events if 'native_result' in row]
    if any(row['state']!='passed' for row in results):return 'native_phase_failed_inspect_report'
    if len(requested)>len(results):return 'native_phase_in_progress'
    if phase not in phases:return 'phase_not_selected'
    if phase in requested:return 'inspect_prior_phase_no_replay'
    if phase!=phases[len(requested)]:return 'selected_phase_order_required'
    return None


def control(context,stop,ready):
    resource.setrlimit(resource.RLIMIT_CORE,(0,0));credential=None;events=[];seen=set();connections=[]
    def connect(path):
        deadline=time.monotonic()+180
        while not path.exists():
            if stop.wait(.2) or time.monotonic()>deadline:raise TimeoutError('assistant_transport')
        stream=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);stream.settimeout(180);stream.connect(str(path));connections.append(stream);return stream
    def save():atomic(context/'control-state.json',{'events':events,'seen_request_ids':sorted(seen)})
    try:
        auth=connect(context/'auth');private=auth.makefile('rwb',buffering=0)
        assert private.readline(64)==b'READY\n'
        credential=''.join(secrets.choice('abcdefghijklmnopqrstuvwxyz') for _ in range(24))
        private.write(credential.encode()+b'\n');assert private.readline(64)==b'CONFIGURED\n'
        qmp=connect(context/'q');q=qmp.makefile('rwb',buffering=0);assert 'QMP' in json.loads(q.readline())
        def call(name,args=None):
            q.write((json.dumps({'execute':name,**({'arguments':args} if args else {})})+'\n').encode())
            while True:
                response=json.loads(q.readline())
                if 'event' in response:continue
                assert 'return' in response,'QMP request refused';return response['return']
        call('qmp_capabilities')
        listener=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);connections.append(listener);listener.bind(str(context/'control'));os.chmod(context/'control',0o600);listener.listen(1);listener.settimeout(.2)
        auth.settimeout(.05);buffer=b'';ready.set();events.append({'state':'private-input-ready'});save()
        while not stop.is_set():
            try:
                data=auth.recv(65536)
                if data:buffer+=data
                if len(buffer)>1024**2:raise ValueError('assistant_private_result_bound')
                while b'\n' in buffer:
                    line,buffer=buffer.split(b'\n',1)
                    if line.startswith(b'INPUT '):
                        request=json.loads(line[6:]);event=request.get('event');code=request.get('code')
                        if set(request)!={'event','code'} or event not in ('key','down','up','capture') or code not in ('spc','ret','home','down','up'):raise ValueError('assistant_native_requested_input')
                        if event=='capture':
                            name='assistant-voice-'+str(len(events))+'.ppm';call('screendump',{'filename':'/work/'+name});events.append({'native_voice_frame':name})
                        elif event=='key':call('send-key',{'keys':[{'type':'qcode','data':code}],'hold-time':80})
                        else:call('input-send-event',{'events':[{'type':'key','data':{'down':event=='down','key':{'type':'qcode','data':code}}}]})
                        private.write(b'INPUT-ACK\n');events.append({'actual_native_QMP_event':event,'code':code})
                    elif line.startswith(b'RESULT '):events.append({'native_result':json.loads(line[7:])})
                    else:events.append({'native_state':line.decode()})
                    save()
            except socket.timeout:pass
            try:client,_=listener.accept()
            except socket.timeout:continue
            with client:
                client.settimeout(5);request=json.loads(client.recv(4096));identity=request.get('request_id')
                if not isinstance(identity,str) or not __import__('re').fullmatch('[a-z0-9-]{1,64}',identity) or identity in seen:client.sendall(b'{"error":"inspect_prior_request_no_replay"}');continue
                seen.add(identity);action=request.get('action');reply={}
                if action=='capture':
                    name='assistant-'+identity+'.ppm';call('screendump',{'filename':'/work/'+name});reply={'frame':name}
                elif action in ('username','password'):
                    # Password is explicit, typed only when the coordinator has
                    # inspected the actual native password/authentication field.
                    value=hook.OWNER if action=='username' else credential
                    for char in value:call('send-key',{'keys':[{'type':'qcode','data':code} for code in key_codes(char)],'hold-time':60});time.sleep(.10)
                    reply={'private_input_sent':action}
                elif action in ('key','shortcut'):
                    codes=['meta_l','shift','t'] if action=='shortcut' else request.get('codes')
                    allowed={'ret','esc','tab','spc','backspace','up','down','left','right','home','end','ctrl','alt','shift','meta_l','f4','f5','f9','f10','f11',*'abcdefghijklmnopqrstuvwxyz'}
                    if not isinstance(codes,list) or not 1<=len(codes)<=3 or any(code not in allowed for code in codes):raise ValueError('assistant_key')
                    call('send-key',{'keys':[{'type':'qcode','data':code} for code in codes],'hold-time':80});reply={'key_sent':True}
                elif action in ('key-down','key-up'):
                    code=request.get('code')
                    if code not in ('spc','ret'):raise ValueError('assistant_hold_key')
                    call('input-send-event',{'events':[{'type':'key','data':{'down':action=='key-down','key':{'type':'qcode','data':code}}}]});reply={'held_key':code,'down':action=='key-down'}
                elif action=='phase':
                    phase=request.get('phase')
                    if phase not in hook.PHASES:raise ValueError('assistant_phase')
                    status_path=HERE.parents[1]/'status.json';status=json.loads(status_path.read_text())
                    phase_error=phase_request_error(json.loads((context/'selected-phases.json').read_text()),events,phase)
                    if phase_error:reply={'error':phase_error,'phase':phase}
                    elif not phase_eligible(phase,status):reply={'error':'story_prerequisite_not_completed','phase':phase}
                    elif subprocess.check_output(['git','status','--porcelain','--','status.json'],cwd=HERE.parents[1],text=True).strip():reply={'error':'commit_reviewed_story_status_first','phase':phase}
                    else:
                        private.write(('PHASE '+phase+'\n').encode());reply={'phase_requested':phase,'native_postcondition_pending':True,'status_sha256':hook.sha(status_path)}
                elif action=='done':
                    requested=sum('phase_requested' in row.get('result',{}) for row in events)
                    returned=sum('native_result' in row for row in events)
                    if requested>returned:reply={'error':'native_phase_in_progress'}
                    else:private.write(b'DONE\n');reply={'finish_requested':True}
                else:raise ValueError('assistant_control_action')
                events.append({'request_id':identity,'action':action,'result':reply});save();client.sendall(json.dumps(reply).encode())
    except Exception as error:
        events.append({'error':type(error).__name__,'scope':'Private input/transport stopped; inspect retained native report. No credential or raw QMP payload logged.'});save();ready.set()
    finally:
        credential=None
        for connection in connections:connection.close()


def send(context,request):
    if not context.is_absolute() or context.resolve()!=context or not context.is_dir() or context.stat().st_uid!=os.getuid() or context.stat().st_mode&0o077:raise ValueError('assistant_private_context')
    with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as client:
        client.settimeout(10);client.connect(str(context/'control'));client.sendall(json.dumps(request).encode());return json.loads(client.recv(65536))


def run_native(manifest_path,generation):
    import boot_test as boot
    from phase2_native_glycin import compressed_payload
    from phase2_native_report import decode
    import phase2_vm,phase2_candidate_vm as candidate,vm
    root=vm.ROOT
    if not __import__('re').fullmatch('[a-z0-9][a-z0-9-]{0,31}',generation):raise ValueError('assistant_generation')
    context=root/'.local/phase2'/('native-assistant-'+generation)
    if context.exists():raise ValueError('Inspect actual context/container/image; never replay')
    if subprocess.check_output(['git','status','--porcelain'],cwd=root,text=True).strip():raise ValueError('Commit reviewed inputs first')
    if __import__('shutil').disk_usage(root).free<100*1024**3+512*1024**2:raise ValueError('assistant_cold_reserve')
    status=json.loads((root/'status.json').read_text())
    if status.get('owner_review',{}).get('phase_2_approved') is not True:raise ValueError('assistant_recorded_owner_authorization_required')
    value=json.loads(manifest_path.read_text())
    if 'voice-device' in value['phases']:
        fixtures=root/'tests/fixtures/voice/human';value['human_samples']={'manifest':json.loads((fixtures/'manifest.json').read_text()),**{locale:base64.b64encode((fixtures/(locale+'.wav')).read_bytes()).decode() for locale in ('en','pt-BR')}}
    hook.validate_manifest(value)
    source=candidate.WORK/'lfs-target.qcow2'
    if value['source_image']!=str(source) or candidate.identity(source)!=value['source_identity']:raise ValueError('assistant_candidate_cold_identity')
    baseline=candidate.bases()
    accepted={row['name']:row for row in json.loads((root/'docs/evidence/B02-desktop-runtime-manifest.json').read_text())['components']}
    for name,row in value['packages'].items():
        if row['archive_path'] is None:
            old=accepted.get(name)
            if old is None or (old['version'],old['archive_sha256'],old['component_record_sha256'])!=(row['version'],row['archive_sha256'],row['record_sha256']):raise ValueError('assistant_new_native_archive_evidence_required')
    if value['B02_manifest_sha256']!=hook.sha(root/'docs/evidence/B02-desktop-runtime-manifest.json'):raise ValueError('assistant_accepted_B02_reference')
    lock=open(vm.VM/'native-boot-test.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);boot.refuse_running_tests();phase2_vm.require_quiescent()
    if subprocess.check_output(['docker','ps','-q','--filter','label=toddy.candidate=phase2-candidate'],text=True).strip():raise ValueError('Stop and reconcile candidate before native GUI boot')
    cold=sorted(candidate.WORK.glob('stop-*.json'))
    stopped=json.loads(cold[-1].read_text()) if cold else {}
    if stopped.get('phase')!='cold' or stopped.get('accepted_B02_unchanged') is not True or stopped.get('candidate_disks',{}).get('lfs-target.qcow2')!=value['source_identity']:raise ValueError('assistant_candidate_cold_receipt')
    data=packet(value,(HERE/'phase2-native-assistant-hook.py').read_text());offset=19+8;packed_sha=data[offset:offset+32].hex()
    context.mkdir(mode=0o700);atomic(context/'selected-phases.json',value['phases']);(context/'inputs.raw').write_bytes(data);(context/'inputs.raw').chmod(0o400)
    unit=(HERE/'desktop-boot-probe.service').read_bytes().replace(b'RuntimeMaxSec=900',b'RuntimeMaxSec=1800')
    payloads={'systemd.extra-unit.toddy-boot-probe.service':unit,'systemd.unit-dropin.multi-user.target':(HERE/'boot-probe.target.conf').read_bytes(),'toddy.boot-probe':compressed_payload(starter(packed_sha))}
    qemu=boot.qemu_arguments('bios',payloads)
    qemu+=['-serial','file:/work/native-evidence.log','-vga','virtio','-device','qemu-xhci,id=usb','-device','usb-tablet,bus=usb.0','-device','usb-kbd,bus=usb.0','-qmp','unix:/work/q,server=on,wait=off','-chardev','socket,id=fixture,path=/work/auth,server=on,wait=off','-device','isa-serial,chardev=fixture,index=2','-drive','file=/work/inputs.raw,if=none,id=asstin,format=raw,readonly=on','-device','virtio-blk-pci,drive=asstin,serial='+hook.SERIAL]
    qemu[qemu.index('-cpu')+1]='host';qemu[qemu.index('-smp')+1]='4';qemu[qemu.index('-m')+1]='12288'
    image=subprocess.check_output(['docker','image','inspect','--format','{{.Id}}',vm.IMAGE],text=True).strip();run_id=uuid.uuid4().hex
    common=['--user',f'{os.getuid()}:{os.getgid()}','--cap-drop=ALL','--security-opt=no-new-privileges','--network=none','--read-only','-v',f'{vm.VM}:/vm:ro','-v',f'{context}:/work']
    state={'guest_memory_mib':12288,'qualification_resource_scope':'Actual12GiB guest; not an8GiB product resource acceptance','candidate_cold_receipt_sha256':hook.sha(cold[-1]),'candidate_source_path':str(source),'phase':'prepared','source_identity':value['source_identity'],'accepted_B02':baseline,'manifest_sha256':hook.sha(manifest_path),'packet_sha256':hashlib.sha256(data).hexdigest(),'commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),'controller_pid':os.getpid(),'controller_boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'controller_start_ticks':Path('/proc/self/stat').read_text().split()[21]}
    atomic(context/'result.json',state)
    with (context/'prepare.log').open('x') as log:
        for command in (['qemu-img','check','/vm/phase2-candidate/lfs-target.qcow2'],['qemu-img','create','-f','qcow2','-F','qcow2','-b','/vm/phase2-candidate/lfs-target.qcow2','/work/target.qcow2']):subprocess.run(['docker','run','--rm',*common,image,*command],check=True,stdout=log,stderr=subprocess.STDOUT)
    cid=subprocess.check_output(['docker','create','--name','toddy-asst-'+run_id[:12],'--label','toddy.boot-test='+run_id,*common,'--device','/dev/kvm','--group-add',str(Path('/dev/kvm').stat().st_gid),'--memory','13g','--cpus','4',image,*qemu],text=True).strip()
    state.update(phase='native-created',container_id=cid,run_id=run_id);atomic(context/'result.json',state)
    stop=threading.Event();ready=threading.Event();controller=threading.Thread(target=control,args=(context,stop,ready),daemon=True)
    subprocess.run(['docker','start',cid],check=True,capture_output=True);controller.start()
    try:
        waited=subprocess.run(['docker','wait',cid],capture_output=True,text=True,timeout=1860)
        state['docker_wait']={'exit':waited.returncode,'stdout':waited.stdout,'stderr':waited.stderr};waited.check_returncode()
        if waited.stdout.strip()!='0':raise ValueError('assistant_actual_QEMU_exit')
    finally:
        stop.set();controller.join(timeout=10);state['container_final_state']=boot.stop_owned_container(cid,run_id);state['phase']='native-stopped';atomic(context/'result.json',state)
    if candidate.identity(source)!=value['source_identity'] or candidate.bases()!=baseline:raise ValueError('assistant_backing_changed')
    report,summary,recovered=decode((context/'native-evidence.log').read_text(errors='strict'));atomic(context/'native-report.json',report)
    state.update(phase='reported',summary=summary,recovered_markers=recovered,backing_unchanged=True);atomic(context/'result.json',state)
    if summary['all_selected_exits_zero'] is not True:raise ValueError('Actual selected phase failure; evidence retained, no acceptance')


def bind_inputs(path,generation):
    """Read back actual builder receipt, then bind its final cold candidate only."""
    import phase2_candidate_vm as candidate
    value=json.loads(path.read_text());hook.validate_manifest(value)
    if not __import__('re').fullmatch('[a-z0-9][a-z0-9-]{0,31}',generation):raise ValueError('assistant_bind_generation')
    if subprocess.check_output(['docker','ps','-q','--filter','label=toddy.candidate=phase2-candidate'],text=True).strip():raise ValueError('assistant_bind_requires_clean_candidate_poweroff')
    candidate.bases();source=candidate.WORK/'lfs-target.qcow2';identity=candidate.identity(source)
    cold=sorted(candidate.WORK.glob('stop-*.json'));stopped=json.loads(cold[-1].read_text()) if cold else {}
    if stopped.get('phase')!='cold' or stopped.get('accepted_B02_unchanged') is not True or stopped.get('candidate_disks',{}).get('lfs-target.qcow2')!=identity:raise ValueError('assistant_bind_cold_candidate_receipt')
    value['source_image']=str(source);value['source_identity']=identity
    destination=candidate.ROOT/'.local/phase2'/('native-assistant-inputs-'+generation+'.json')
    with destination.open('x') as stream:os.fchmod(stream.fileno(),0o600);json.dump(value,stream,indent=2);stream.write('\n')
    return destination


def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='operation',required=True)
    run=sub.add_parser('run');run.add_argument('--manifest',type=Path,required=True);run.add_argument('--generation',required=True)
    bind=sub.add_parser('bind');bind.add_argument('--inputs',type=Path,required=True);bind.add_argument('--generation',required=True)
    action=sub.add_parser('send');action.add_argument('--context',type=Path,required=True);action.add_argument('--request-id',required=True);action.add_argument('--action',choices=['capture','username','password','key','shortcut','key-down','key-up','phase','done'],required=True);action.add_argument('--phase',choices=hook.PHASES);action.add_argument('--codes',nargs='+');action.add_argument('--code')
    args=parser.parse_args()
    if args.operation=='run':run_native(args.manifest,args.generation)
    elif args.operation=='bind':print(bind_inputs(args.inputs,args.generation))
    else:print(json.dumps(send(args.context,{key:value for key,value in vars(args).items() if key not in ('operation','context') and value is not None})))

if __name__=='__main__':main()

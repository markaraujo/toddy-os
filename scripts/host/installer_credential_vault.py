"""RAM-only disposable-owner credential typing; never returns a credential."""
import hashlib,json,os,re,socket,stat,subprocess,sys,time
from pathlib import Path
import installed_owner_boot as installed
import phase2_vm


def safe_file(path):
    info=path.lstat()
    if path.resolve()!=path or not stat.S_ISREG(info.st_mode) or info.st_uid!=os.getuid() or info.st_nlink!=1 or info.st_mode&0o022:raise ValueError('owned_credential_observation_file_required')
    return path


def auth_ready(row,handoff,number):
    if not isinstance(row,dict) or row.get('version')!=1 or row.get('round')!=number or row.get('recovery') is not (number==3) or row.get('root_uuid')!=handoff['root_uuid'] or row.get('owner_uid')!=handoff['expected_owner']['uid'] or row.get('state')!='authentication-wait' or row.get('owner_active') is not False or not isinstance(row.get('sequence'),int) or row['sequence']<=0 or not re.fullmatch('[a-f0-9-]{36}',row.get('boot_id','')):raise ValueError('fresh_actual_authentication_wait_required')
    if number==3:
        tty=row.get('tty')
        if not isinstance(tty,dict) or tty.get('name')!='tty2' or tty.get('echo') is not False or type(tty.get('foreground_login_pid')) is not int or tty['foreground_login_pid']<=1:raise ValueError('actual_noecho_foreground_tty_login_required')
    else:
        greeter=row.get('greeter',{})
        if not isinstance(greeter,dict) or greeter.get('Name')!='gdm' or greeter.get('Active')!='yes' or greeter.get('Remote')!='no' or greeter.get('Class')!='greeter' or greeter.get('Type')!='wayland' or greeter.get('Service')!='gdm-launch-environment' or not isinstance(row.get('pam_worker_pid'),int) or row['pam_worker_pid']<=1:raise ValueError('actual_gdm_password_conversation_required')
    return row


def latest_auth(context,handoff,number):
    path=safe_file(context/('observation-'+str(number)+'.log'))
    if time.time_ns()-path.stat().st_mtime_ns>3*10**9:raise ValueError('fresh_guest_observer_update_required')
    with path.open('rb') as stream:
        stream.seek(max(0,path.stat().st_size-65536));raw=stream.read(65536).decode('utf-8',errors='strict')
    if 'TODDY_INSTALLED_OWNER ' in raw:raise ValueError('completed_or_failed_owner_observation_no_typing')
    rows=[line.removeprefix('TODDY_INSTALLED_AUTH ') for line in raw.splitlines() if line.startswith('TODDY_INSTALLED_AUTH ')]
    if not rows:raise ValueError('actual_authentication_observer_missing')
    return auth_ready(json.loads(rows[-1]),handoff,number)


def owned_context(context,handoff,source_context):
    root=installed.ROOT/'.local/phase2'
    if not context.is_absolute() or context.parent!=root or not re.fullmatch('installed-owner-[a-z0-9-]{1,32}',context.name):raise ValueError('fixed_owned_installed_context_required')
    installed.private(context,True)
    read=lambda name:json.loads(safe_file(context/name).read_bytes())
    active=read('active.json');number=active['round']
    if number not in (1,2,3) or installed.validate_handoff(read('handoff.json'))!=handoff:raise ValueError('exact_actual_installed_handoff_required')
    inputs=read('inputs.json');cold=json.loads(safe_file(source_context/'cold.json').read_bytes())
    if cold.get('state')!='cold-completed-install' or cold.get('media_detached') is not True or cold.get('vault_sha256')!=installed.boot.digest(Path(__file__)) or inputs['source']['sha256']!=cold['disk_sha256'] or inputs['source']['identity']!=cold['disk_identity'] or phase2_vm.backing_identity(installed.SOURCE)!=cold['disk_identity'] or installed.SOURCE.stat().st_ctime_ns!=cold['disk_ctime_ns']:raise ValueError('exact_cold_source_disk_required')
    if inputs['producer_sha256']!=installed.boot.digest(Path(installed.__file__)) or inputs['public_sources'].get('installed-auth-wait.py')!=installed.boot.digest(Path(__file__).with_name('installed-auth-wait.py')):raise ValueError('frozen_installed_observer_controller_required')
    intent=read('intent-'+str(number)+'.json');pin={key:value for key,value in phase2_vm.backing_identity(context/'target.qcow2').items() if key in ('device','inode')}
    if pin!=intent.get('overlay_pin') or intent['run_id']!=active['run_id']:raise ValueError('actual_owned_overlay_identity_required')
    row=json.loads(subprocess.check_output(['docker','inspect',active['container_id']],text=True))[0]
    mounts={(item['Source'],item['Destination'],item['RW']) for item in row['Mounts'] if item['Type']=='bind'}
    if row['Config']['Labels'].get('toddy.boot-test')!=active['run_id'] or not row['State']['Running'] or row['Config']['Cmd']!=installed.qemu(handoff,number,number==3) or row['Config']['Image']!=inputs['container_image'] or mounts!={(str(installed.SOURCE),'/installed/source.qcow2',False),(str(context),'/work',True)} or row['HostConfig']['NetworkMode']!='none':raise ValueError('exact_owned_installed_vm_required')
    return number


def type_into_owned_context(secret,context,handoff,source_context,frame_sha,seen):
    number=owned_context(context,handoff,source_context);auth=latest_auth(context,handoff,number)
    identity=(str(context),number,auth['boot_id'])
    if identity in seen:raise ValueError('private_typing_already_intended_no_automatic_retry')
    frame=json.loads(safe_file(context/('input-frame-'+str(number)+'.json')).read_bytes())
    if not isinstance(frame.get('frame'),str) or not re.fullmatch(r'frame-[a-f0-9]{32}\.ppm',frame['frame']):raise ValueError('actual_owned_frame_filename_required')
    path=safe_file(context/frame['frame'])
    if frame.get('round')!=number or frame.get('sha256')!=frame_sha or installed.boot.digest(path)!=frame_sha or time.time_ns()-path.stat().st_mtime_ns>30*10**9:raise ValueError('fresh_inspected_actual_password_frame_required')
    seen.add(identity)  # Holds even if a later QMP acknowledgement is lost.
    with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as stream:
        stream.settimeout(5);stream.connect(str(context/('q-'+str(number))));wire=stream.makefile('rwb',buffering=0);json.loads(wire.readline())
        def call(command):
            wire.write(json.dumps(command).encode()+b'\n')
            while True:
                result=json.loads(wire.readline())
                if 'error' in result:raise ValueError('private_input_qmp_outcome_uncertain')
                if 'return' in result:return
        call({'execute':'qmp_capabilities'})
        for char in secret:
            current=latest_auth(context,handoff,number)
            if current['boot_id']!=auth['boot_id']:raise ValueError('guest_authentication_boot_changed')
            call({'execute':'send-key','arguments':{'keys':[{'type':'qcode','data':code} for code in installed.key_codes(char)],'hold-time':60}});time.sleep(.1)
    return {'private_input_typed':True,'authentication_observed':False,'round':number,'boot_id':auth['boot_id']}


def serve(secret,handoff,source_context,save):
    deadline=time.monotonic()+7200;seen=set();events=[];path=source_context/'credential-vault'
    with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as server:
        server.bind(str(path));os.chmod(path,0o600);server.listen(1);server.settimeout(.5)
        save(source_context/'credential-state.json',{'state':'RAM-only-qualification-credential-available','pid':os.getpid(),'max_lifetime_seconds':7200,'secret_persisted':False})
        try:
            while time.monotonic()<deadline:
                try:client,_=server.accept()
                except socket.timeout:continue
                with client:
                    client.settimeout(5)
                    try:
                        peer=client.getsockopt(socket.SOL_SOCKET,socket.SO_PEERCRED,12)
                        if int.from_bytes(peer[4:8],sys.byteorder)!=os.getuid():raise ValueError('same_uid_vault_only')
                        request=json.loads(client.recv(4096))
                        if request=={'action':'close'}:
                            client.sendall(b'{"state":"RAM-credential-service-closing","credential_returned":false}');return
                        if set(request)!={'action','context','frame_sha256'} or request['action']!='type' or not re.fullmatch('[a-f0-9]{64}',request['frame_sha256']):raise ValueError('fixed_type_only_vault_action')
                        result=type_into_owned_context(secret,Path(request['context']),handoff,source_context,request['frame_sha256'],seen)
                    except Exception as error:result={'error':str(error) if isinstance(error,ValueError) else type(error).__name__,'credential_returned':False}
                    events.append({'time_ns':time.time_ns(),'result':result});save(source_context/'credential-events.json',{'events':events})
                    client.sendall(json.dumps(result).encode())
        finally:
            secret=None;save(source_context/'credential-state.json',{'state':'fixture-credential-unavailable-no-password-reset','secret_persisted':False,'new_fixture_required':True})
            path.unlink()

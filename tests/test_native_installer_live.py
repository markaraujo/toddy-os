"""Source-only disposable controller fixtures; never starts VM or writes a disk."""
import ast,copy,fcntl,hashlib,importlib.util,json,os,socket,sys,tempfile,threading,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts/host'))
import native_installer_live as c
import installer_input_snapshot as snapshot
import installer_credential_vault as vault
from runtime.installer.disk_plan import make_plan
spec=importlib.util.spec_from_file_location('live_probe_fixture',ROOT/'scripts/host/installer-live-probe.py')
probe=importlib.util.module_from_spec(spec);spec.loader.exec_module(probe)


def fixture():
    options={'operation_id':'a'*32,'boot_mode':'bios','username':'owner','uid':1000,'gid':1000,'locale':'en_US.UTF-8','timezone':'UTC','hostname':'toddy-owner','ai_choice':'later','extras':[]}
    disk={'path':'/dev/fixture','major_minor':'253:16','serial':c.SERIAL,'size':64*1024**3,'sector_size':512,'model':'QEMU HARDDISK','driver':'virtio_blk','readonly':False,'mounted':False,'blank':True,'virtual':True}
    plan=make_plan(disk,options,{'sha256':'b'*64,'catalog_sha256':'d'*64,'bytes':2*1024**3})
    return options,{'state':'qualification-review-only','disk_writes':False,'plan':plan},{'payload_manifest_sha256':'b'*64,'policy_sha256':'c'*64,'image_manifest_sha256':'e'*64}


class InstallerControllerTests(unittest.TestCase):
    def test_real_iso_boot_owned_devices_and_network_none_command_shape(self):
        for firmware in ('bios','uefi'):
            args=c.qemu(firmware,'a'*64)
            self.assertNotIn('-kernel',args);self.assertNotIn('/dev/sda',' '.join(args))
            self.assertIn('order=d,strict=on',args)
            self.assertIn('virtio-blk-pci,drive=root,serial=TODDY-INSTALL-P2-1',args)
            self.assertIn('file=/live/live.iso,format=raw,media=cdrom,readonly=on',args)
            self.assertIn('file=/inputs/inputs.iso,if=none,id=inputs,format=raw,readonly=on',args)
            self.assertEqual(args[args.index('-nic')+1],'none')
            self.assertTrue(all(len(item)<16384 for item in args if 'credential.binary:' in item))
    def test_precise_live_review_requires_actual_serial_blank_64g_and_options(self):
        options,review,descriptor=fixture();self.assertEqual(c.review_valid(review,options,descriptor),review['plan'])
        for field,value in [('serial','HOST-PHYSICAL-DISK'),('size',32*1024**3),('virtual',False),('blank',False)]:
            changed=copy.deepcopy(review);changed['plan']['target'][field]=value
            with self.assertRaises(ValueError):c.review_valid(changed,options,descriptor)
        with self.assertRaises(ValueError):c.review_valid(dict(review,password='never accepted'),options,descriptor)
    def test_exact_confirmation_precedes_private_password_and_unknown_execute_is_held(self):
        options,review,descriptor=fixture();inputs={'descriptor':descriptor}
        with patch.object(c,'read',return_value=review):
            with self.assertRaisesRegex(ValueError,'explicit_reviewed'):c.control_request({'action':'execute','request_id':'one','confirm':'f'*64},inputs,options,[])
            request={'action':'execute','request_id':'one','confirm':review['plan']['plan_sha256'],'generated':True}
            self.assertTrue(c.control_request(request,inputs,options,[])['generated'])
            with self.assertRaisesRegex(ValueError,'uncertain_execute'):c.control_request(dict(request,request_id='two'),inputs,options,[{'action':'execute','request_id':'old','state':'transport-intended'}])
            with self.assertRaisesRegex(ValueError,'no_replay'):c.control_request(request,inputs,options,[{'action':'review','request_id':'one'}])
    def test_cancel_is_a_fixed_request_and_never_an_effect_rollback_claim(self):
        self.assertEqual(c.control_request({'action':'cancel','request_id':'stop'}, {},{},[])['action'],'cancel')
        for action in ('root-command','reset-password','retry','format-host'):
            with self.assertRaises(ValueError):c.control_request({'action':action,'request_id':'bad'}, {},{},[])
        with self.assertRaises(ValueError):c.control_request({'action':'cancel','request_id':'stop','password':'must not travel'}, {},{},[])
    def test_running_or_uncollected_complete_operation_cannot_finish(self):
        with self.assertRaisesRegex(ValueError,'terminal'):c.control_request({'action':'finish','request_id':'finish'}, {},{},[{'action':'execute'}])
        with patch.object(c.Path,'exists',return_value=False):
            with self.assertRaisesRegex(ValueError,'nine_reports'):c.control_request({'action':'finish','request_id':'finish'}, {},{},[{'action':'execute'},{'guest':{'event':'execute-ended','result':{'state':'completed'}}}])
    def test_host_capacity_and_storage_measurement_are_not_optional(self):
        with self.assertRaises(ValueError):c.admission(10**15,{})
        storage={'root_storage_bound_bytes':12*1024**3};threshold=c.HOST_FLOOR+28*1024**3
        self.assertFalse(c.admission(threshold-1,storage));self.assertTrue(c.admission(threshold,storage))
    def test_root_source_guard_fails_before_any_vm_command(self):
        before=os.umask(0o022);os.umask(before)
        self.addCleanup(os.umask,before)
        with patch.object(c.os,'getuid',return_value=0),patch.object(c.subprocess,'check_output',side_effect=AssertionError('No VM call')):
            with self.assertRaisesRegex(ValueError,'nonroot'):c.run(Path('/unqualified.iso'),'a'*64,Path('/fixture.json'))
        self.assertEqual(os.umask(before),before)
    def test_detached_boot_requires_successful_poststop_cold_receipt_not_saved_handoff(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);root.chmod(0o700);source=root/'installed.qcow2';source.write_bytes(b'unqualified fixture only');source.chmod(0o600)
            from tests.test_installed_owner_boot import handoff
            path=root/'handoff.json';path.write_text(json.dumps(handoff()));path.chmod(0o600)
            with patch.object(c.installed,'SOURCE',source):
                with self.assertRaises(FileNotFoundError):c.installed.cold_handoff(path)
                cold=root/'cold.json';cold.write_text(json.dumps({'version':1,'kind':'native-live-install-cold-handoff-v1','state':'cold-without-install-acceptance'}));cold.chmod(0o600)
                with self.assertRaisesRegex(ValueError,'actual_cold_completed'):c.installed.cold_handoff(path)

    def test_missing_actual_reports_never_create_handoff(self):
        with self.assertRaisesRegex(ValueError,'ten_installer'):c.evidence({'state':'actual-evidence-collected','files':{}},{},{})
    def test_sealed_plan_descriptor_is_actual_kernel_sealed_and_no_password_field(self):
        fd=probe.sealed(b'{"unqualified_source_fixture":true}')
        try:
            from runtime.installer.calamares.adapter import sealed_json
            self.assertEqual(sealed_json(fd,uid=os.geteuid()),{'unqualified_source_fixture':True})
            with self.assertRaises(PermissionError):os.write(fd,b'changed')
            self.assertTrue(fcntl.fcntl(fd,fcntl.F_GET_SEALS)&fcntl.F_SEAL_WRITE)
        finally:os.close(fd)
    def test_probe_preserves_actual_runtime_cancellation_and_no_root_autologin(self):
        source=(ROOT/'scripts/host/installer-live-probe.py').read_text()
        self.assertIn("'--credential-fd'",source);self.assertIn("'--cancel-fd'",source)
        self.assertIn('harness.NativeInputs()',source);self.assertIn('live.authorize_live_owner(1000)',source)
        self.assertIn('source.backup(target)',source);self.assertNotIn('chpasswd',source)
        self.assertNotIn('LinuxDisk=',source);self.assertNotIn('OnSuccess=poweroff',c.SERVICE.decode())
        self.assertIn('PrivateMounts=yes',c.SERVICE.decode());self.assertIn('KillMode=mixed',c.SERVICE.decode())
    def test_auxiliary_snapshot_requires_canonical_source_and_no_dirty_tree_copy(self):
        source=(ROOT/'scripts/host/installer_input_snapshot.py').read_text()
        self.assertIn('p.component_from_record',source);self.assertIn('Frozen installed runtime source differs',source)
        self.assertIn('-graft-points',source);self.assertIn('--set_all_file_dates',source);self.assertIn('-no_rc',source)
        self.assertNotIn('copytree',source);self.assertNotIn("'/etc'",source)


class CredentialVaultTests(unittest.TestCase):
    def row(self,number=1):
        return {'version':1,'round':number,'recovery':number==3,'root_uuid':'abcd-1234','owner_uid':1000,'state':'authentication-wait','owner_active':False,'sequence':1,'boot_id':'1'*8+'-'+'1'*4+'-'+'1'*4+'-'+'1'*4+'-'+'1'*12,
            'greeter':{'User':'42','Name':'gdm','Active':'yes','Remote':'no','Type':'wayland','Class':'greeter','Service':'gdm-launch-environment'},'pam_worker_pid':123,'tty':{'name':'tty2','echo':False,'foreground_login_pid':125}}
    def test_actual_greeter_pam_or_noecho_tty_required_before_private_typing(self):
        handoff={'root_uuid':'abcd-1234','expected_owner':{'uid':1000}}
        for number in (1,2,3,4):self.assertEqual(vault.auth_ready(self.row(number),handoff,number)['state'],'authentication-wait')
        for key,value in [('owner_active',True),('root_uuid','foreign'),('state','owner-session-active'),('round',2),('pam_worker_pid',None),('greeter',None)]:
            changed=self.row();changed[key]=value
            with self.assertRaises(ValueError):vault.auth_ready(changed,handoff,1)
        changed=self.row(3);changed['tty']['echo']=True
        with self.assertRaisesRegex(ValueError,'noecho'):vault.auth_ready(changed,handoff,3)
    def test_missing_or_stale_observer_and_completed_desktop_deny_secret(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);path=root/'observation-1.log';path.write_text('TODDY_INSTALLED_AUTH '+json.dumps(self.row())+'\n');path.chmod(0o600)
            handoff={'root_uuid':'abcd-1234','expected_owner':{'uid':1000}}
            self.assertEqual(vault.latest_auth(root,handoff,1)['sequence'],1)
            path.write_text(path.read_text()+'TODDY_INSTALLED_OWNER {"state":"observed"}\n')
            with self.assertRaisesRegex(ValueError,'completed'):vault.latest_auth(root,handoff,1)
            os.utime(path,(1,1))
            with self.assertRaisesRegex(ValueError,'fresh'):vault.latest_auth(root,handoff,1)
    def test_observer_code_changes_no_pam_login_or_session_policy(self):
        source=(ROOT/'scripts/host/installed-auth-wait.py').read_text();ast.parse(source)
        self.assertIn('termios.ECHO',source);self.assertIn('owner-session-active',source)
        for forbidden in ('chpasswd','useradd','loginctl activate','xhost','setuid','subprocess.run'):
            self.assertNotIn(forbidden,source)
        payload=c.installed.payloads({'fixture':'unqualified'},1,False)['toddy.boot-probe']
        self.assertLess(len(payload),12288)
    def test_actual_private_socket_has_no_secret_return_action_and_closes_without_persistence(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);ready=threading.Event()
            def save(path,value):
                path.write_text(json.dumps(value));path.chmod(0o600)
                if value.get('state')=='RAM-only-qualification-credential-available':ready.set()
            thread=threading.Thread(target=vault.serve,args=('synthetic-fixture-secret-only',{},root,save));thread.start()
            self.assertTrue(ready.wait(2))
            self.assertEqual((root/'credential-vault').stat().st_mode&0o777,0o600)
            def request(body):
                with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as client:
                    client.settimeout(2);client.connect(str(root/'credential-vault'));client.sendall(json.dumps(body).encode());return json.loads(client.recv(4096))
            result=request({'action':'get-password'})
            self.assertFalse(result['credential_returned']);self.assertNotIn('synthetic-fixture-secret-only',json.dumps(result))
            result=request({'action':'close'});thread.join(2);self.assertFalse(thread.is_alive())
            self.assertFalse((root/'credential-vault').exists())
            self.assertNotIn('synthetic-fixture-secret-only',''.join(path.read_text() for path in root.iterdir()))
    def test_foreign_context_refused_before_any_docker_or_qmp_call(self):
        with patch.object(vault.subprocess,'check_output',side_effect=AssertionError('No VM command')):
            with self.assertRaisesRegex(ValueError,'fixed_owned'):vault.owned_context(Path('/dev/sda'),{},Path('/unqualified'))
    def test_vault_types_only_and_never_persists_or_returns_password(self):
        source=(ROOT/'scripts/host/installer_credential_vault.py').read_text()
        self.assertIn('SO_PEERCRED',source);self.assertIn('seen.add(identity)',source)
        self.assertIn('latest_auth(context,handoff,number)',source)
        self.assertIn('source_context/\'credential-state.json\'',source)
        self.assertNotIn('write(secret',source);self.assertNotIn('return secret',source)
        self.assertNotIn('password=',source)

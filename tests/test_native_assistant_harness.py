"""Pure source/transport fixtures. No VM, native GUI, model or audio execution."""
import base64,copy,hashlib,importlib.util,io,json,socket,sys,tempfile,threading,time,unittest,zlib
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
def module(name,file):
    spec=importlib.util.spec_from_file_location(name,ROOT/'scripts/host'/file)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value
h=module('assistant_test_hook','phase2-native-assistant-hook.py')
c=module('assistant_test_control','phase2-native-assistant-control.py')


def manifest():
    packages={}
    for name in ('toddy-assistant','toddy-agent','toddy-executor'):
        record={'packaging_backend':{'kind':'source-built-native-dpkg'},'name':name,'version':'0.2.0-1+toddy1','installed':True,'archive_sha256':'1'*64,'payload':{'/usr/lib/toddy/fixture':{'mode':33188,'sha256':'2'*64}},'scope':'Unqualified source fixture only'}
        packages[name]={'version':record['version'],'archive_sha256':record['archive_sha256'],'record_sha256':hashlib.sha256((json.dumps(record,indent=2)+'\n').encode()).hexdigest(),'record':record,'record_text':json.dumps(record,indent=2)+'\n','archive_path':'/sources/phase2/assistant-native-inputs/fixture/'+name+'.deb','archive_bytes':100}
    return {'assistant_qualification_version':1,'source_image':'/fixture/cold.qcow2','source_identity':{'scope':'Unqualified fixture'},'kernel':'7.1.8-toddy','kernel_config_sha256':'3'*64,'B02_manifest_sha256':'4'*64,'phases':['ui-prepare','ui-en'],'packages':packages,'files':{},'local_model':None,'human_samples':None}


class ManifestTests(unittest.TestCase):
    def test_source_import_and_embedded_native_client_are_pure_and_compile(self):
        compile(h.USER_CLIENT,'native-client-fixture','exec')
        compile(c.starter('a'*64),'native-loader-fixture','exec')
        self.assertLess(len(zlib.compress(c.starter('a'*64))),8192)
        self.assertLess(len(h.SERIAL),20)
    def test_strict_selected_phase_prerequisites_no_unknown_or_replayed_phase(self):
        self.assertEqual(h.validate_manifest(manifest())['phases'],['ui-prepare','ui-en'])
        for phases in (['memory'],['ui-prepare','ui-en','ui-en'],['ui-prepare','unknown'],['ui-en','ui-prepare']):
            value=manifest();value['phases']=phases
            with self.assertRaisesRegex(ValueError,'phase'):h.validate_manifest(value)
    def test_milestone_gate_requires_actual_completed_dependencies(self):
        status={'owner_review':{'phase_2_approved':True},'milestones':[{'id':'B07','status':'in_progress','depends_on':[]},{'id':'B08','depends_on':['B07']}]}
        self.assertFalse(c.phase_eligible('grant',status))
        status['milestones'][0]['status']='completed';self.assertTrue(c.phase_eligible('grant',status))
        status['owner_review']['phase_2_approved']=False;self.assertFalse(c.phase_eligible('grant',status))
    def test_native_record_bytes_are_bound_and_source_flag_cannot_qualify(self):
        for change in ('payload','installed','unknown'):
            value=manifest();row=value['packages']['toddy-agent']
            if change=='payload':row['record']['payload']['/usr/lib/toddy/fixture']['sha256']='9'*64
            elif change=='installed':row['record']['installed']=False
            else:row['qualified']=True
            with self.assertRaisesRegex(ValueError,'native_package_record|native_record_hash'):h.validate_manifest(value)
    def test_new_package_archive_paths_cannot_escape_fixed_fixture_cache(self):
        for path in ('/etc/shadow','/sources/phase2/assistant-native-inputs/../escape'):
            value=manifest();value['packages']['toddy-agent']['archive_path']=path
            with self.assertRaisesRegex(ValueError,'archive_path'):h.validate_manifest(value)
    def test_actual_native_guard_refuses_host_before_commands(self):
        with patch.object(h.os,'geteuid',return_value=1000),patch.object(h,'command') as command:
            with self.assertRaisesRegex(ValueError,'native_kernel'):h.verify_native(manifest())
            command.assert_not_called()
    def test_model_change_and_unrequested_arbitrary_path_fail_closed(self):
        value=manifest();value['local_model']={'path':'/etc/shadow'}
        with self.assertRaisesRegex(ValueError,'frozen_local_model'):h.validate_manifest(value)
    def test_exact_human_fixture_bytes_are_required_when_provided(self):
        value=manifest();folder=ROOT/'tests/fixtures/voice/human'
        value['human_samples']={'manifest':json.loads((folder/'manifest.json').read_text()),**{locale:base64.b64encode((folder/(locale+'.wav')).read_bytes()).decode() for locale in ('en','pt-BR')}}
        h.validate_manifest(value)
        value['human_samples']['en']=base64.b64encode(b'silent or fake transcript fixture').decode()
        with self.assertRaisesRegex(ValueError,'human_input_hash'):h.validate_manifest(value)
    def test_readonly_packet_reader_checks_exact_hash_and_bounded_manifest(self):
        value=manifest();data=c.packet(value,'# pure test hook; never executed')
        with patch.object(Path,'open',return_value=io.BytesIO(data)):
            self.assertEqual(h.manifest_from_disk(),value)
        changed=bytearray(data);changed[60]^=1
        with patch.object(Path,'open',return_value=io.BytesIO(changed)),self.assertRaisesRegex(ValueError,'input_hash'):
            h.manifest_from_disk()
    def test_fault_injector_refuses_unrelated_actual_process_before_signals(self):
        import os
        proof={};stopped=threading.Event()
        with patch.object(h.subprocess,'run',return_value=type('Reply',(),{'stdout':str(os.getpid())})()),patch.object(h.os,'pidfd_open') as opener,patch.object(h.signal,'pidfd_send_signal') as signal:
            h.interrupt_health_child({},stopped,proof)
            self.assertIn('error',proof);opener.assert_not_called();signal.assert_not_called()
    def test_virtual_audio_source_code_keeps_fixed_qualified_transport(self):
        self.assertIn('media.class = Audio/Sink',h.USER_CLIENT)
        self.assertIn('media.class = Audio/Source',h.USER_CLIENT)
        self.assertIn("controller.request('capture',accepted_pin=catalog.pin",h.USER_CLIENT)
        self.assertIn("bridge('down','spc')",h.USER_CLIENT)
        self.assertIn("bridge('up','spc')",h.USER_CLIENT)
        self.assertIn("tasks_after==tasks_before",h.USER_CLIENT)
        self.assertNotIn('catalog_factory=',h.USER_CLIENT)
        self.assertNotIn('health=',h.USER_CLIENT)


class PrivateTransportTests(unittest.TestCase):
    def test_dummy_private_password_never_enters_receipt_and_request_is_not_replayed(self):
        with tempfile.TemporaryDirectory() as temporary:
            context=Path(temporary);stop=threading.Event();ready=threading.Event();secret=[];calls=[];errors=[]
            auth_server=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);auth_server.bind(str(context/'auth'));auth_server.listen(1)
            qmp_server=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);qmp_server.bind(str(context/'q'));qmp_server.listen(1)
            def auth_fixture():
                try:
                    client,_=auth_server.accept()
                    with client:
                        stream=client.makefile('rwb',buffering=0);stream.write(b'READY\n');secret.append(stream.readline(64).strip());stream.write(b'CONFIGURED\nOWNER-READY\n')
                        while not stop.wait(.05):pass
                except Exception as error:errors.append(type(error).__name__)
            def qmp_fixture():
                try:
                    client,_=qmp_server.accept()
                    with client:
                        client.settimeout(.1);stream=client.makefile('rwb',buffering=0);stream.write(b'{"QMP":{}}\n');buffer=b''
                        while not stop.is_set():
                            try:chunk=client.recv(4096)
                            except socket.timeout:continue
                            if not chunk:break
                            buffer+=chunk
                            while b'\n' in buffer:
                                line,buffer=buffer.split(b'\n',1);calls.append(json.loads(line));stream.write(b'{"return":{}}\n')
                except Exception as error:errors.append(type(error).__name__)
            workers=[threading.Thread(target=auth_fixture),threading.Thread(target=qmp_fixture),threading.Thread(target=c.control,args=(context,stop,ready))]
            for worker in workers:worker.start()
            try:
                self.assertTrue(ready.wait(3));self.assertEqual(len(secret[0]),24)
                reply=c.send(context,{'request_id':'private-auth-once','action':'password'});self.assertEqual(reply,{'private_input_sent':'password'})
                before=len(calls);reply=c.send(context,{'request_id':'private-auth-once','action':'password'})
                self.assertEqual(reply,{'error':'inspect_prior_request_no_replay'});self.assertEqual(len(calls),before)
                data=(context/'control-state.json').read_bytes();self.assertNotIn(secret[0],data)
                self.assertNotIn(b'fixture_password',data)
                self.assertTrue(all(row['execute'] in ('qmp_capabilities','send-key') for row in calls))
            finally:
                stop.set()
                for worker in workers:worker.join(3)
                auth_server.close();qmp_server.close()
            self.assertFalse(any(worker.is_alive() for worker in workers));self.assertFalse(errors)

if __name__=='__main__':unittest.main()

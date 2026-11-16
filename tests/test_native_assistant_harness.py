"""Pure source/transport fixtures. No VM, native GUI, model or audio execution."""
import ast,base64,copy,hashlib,importlib.util,io,json,socket,sys,tempfile,threading,time,unittest,zlib
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
    def test_exact_parent_cached_qwen_and_license_path_match_frozen_contract(self):
        value=manifest();value['local_model']={
            'path':'/sources/phase2/inputs/local-model-proof/model.gguf',
            'sha256':'061b54daade076b5d3362dac252678d17da8c68f07560be70818cace6590cb1a',
            'bytes':1834426016,'license_path':'/sources/qwen-LICENSE',
            'license_sha256':'5de36594c10839788a8c589443a8ef9d8b8d17c65a1b5807206ae037fc36c6bd'}
        h.validate_manifest(value)
        for changed in ('/sources/other-LICENSE','/sources/../qwen-LICENSE','/etc/shadow'):
            value['local_model']['license_path']=changed
            with self.assertRaisesRegex(ValueError,'frozen_local_model'):h.validate_manifest(value)

    def test_literal_service_calls_match_current_production_xml(self):
        import xml.etree.ElementTree as ET
        api={}
        for method in ET.parse(ROOT/'runtime/broker/io.github.markaraujo.Toddy.Service1.xml').findall('.//method'):
            signature=lambda direction:'('+''.join(arg.attrib['type'] for arg in method.findall('arg') if arg.attrib.get('direction')==direction)+')'
            api[method.attrib['name']]=(signature('in'),signature('out'))
        seen=set()
        for node in ast.walk(ast.parse(h.USER_CLIENT)):
            if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id=='call' and node.args and isinstance(node.args[0],ast.Constant):
                name=node.args[0].value;seen.add(name)
                signature=ast.literal_eval(node.args[2]) if len(node.args)>2 else '()'
                self.assertEqual(api[name],(signature,'(s)'),name)
        self.assertTrue({'SubmitTask','MutateMemory','ConfigureIntegration','ConfigureAutomation'}<=seen)

    def test_real_configured_engine_consumes_extracted_local_connection_settings(self):
        from runtime.broker.configured_engine import ConfiguredEngine
        tree=ast.parse(h.USER_CLIENT)
        # Extract the actual guest writer's JSON argument without executing its
        # service, GI, model, GTK or audio code.
        writes=[node for node in ast.walk(tree) if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute) and isinstance(node.func.value,ast.Name) and node.func.value.id=='json' and node.func.attr=='dump']
        payload=next(node.args[0] for node in writes if isinstance(node.args[0],ast.Dict) and any(isinstance(key,ast.Constant) and key.value=='model_path' for key in node.args[0].keys))
        model='/sources/phase2/inputs/local-model-proof/model.gguf'
        settings=eval(compile(ast.Expression(payload),'<extracted-settings>','eval'),{'manifest':{'local_model':{'path':model}}})
        profile=json.loads((ROOT/'config/phase2/profile/config.json').read_text())
        edit=next(node for node in ast.walk(tree) if isinstance(node,ast.FunctionDef) and node.name=='edit' and any(isinstance(child,ast.Constant) and child.value=='qual-local' for child in ast.walk(node)))
        scope={};exec(compile(ast.Module(body=[edit],type_ignores=[]),'<extracted-profile-edit>','exec'),scope);scope['edit'](profile)
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'qual-local.json';path.write_text(json.dumps(settings));path.chmod(0o600)
            engine=ConfiguredEngine(ROOT/'config/phase2',config_directory=directory,adapter=object())
            self.assertEqual(engine.connection_settings(profile),settings)
            self.assertEqual(settings['model_path'],model)

    def test_integration_revoke_uses_production_operation_and_selected_skill(self):
        # The production parser rejects unsupported operations before accessing
        # the profile transaction; no service, plugin or browser is started.
        from contextlib import contextmanager
        from types import SimpleNamespace
        import sqlite3
        from runtime.broker.integrations import Integrations,IntegrationError
        tree=ast.parse(h.USER_CLIENT);operations=[]
        for node in ast.walk(tree):
            if isinstance(node,ast.Dict):
                values={key.value:value.value for key,value in zip(node.keys,node.values) if isinstance(key,ast.Constant) and isinstance(value,ast.Constant)}
                if values.get('id')=='release-reference' and 'operation' in values:operations.append(values['operation'])
        self.assertIn('revoke',operations);self.assertNotIn('disable',operations)
        db=sqlite3.connect(':memory:');self.addCleanup(db.close)
        db.execute('CREATE TABLE integration_approvals(profile_id TEXT,id TEXT)')
        db.execute('INSERT INTO integration_approvals VALUES(?,?)',('fixture','release-reference'))
        @contextmanager
        def transaction():
            with db:yield db
        service=Integrations.__new__(Integrations);service._owner=lambda:None;revoked=[];service.stop_all=revoked.append
        service.profiles=SimpleNamespace(_transaction=transaction,_current=lambda db:'revision',profile_id='fixture')
        for operation in operations:
            result=service.configure('revision',json.dumps({'version':1,'id':'release-reference','operation':operation}))
            self.assertFalse(result['enabled'])
        self.assertEqual(db.execute('SELECT count(*) FROM integration_approvals').fetchone()[0],0)
        self.assertEqual(revoked,['release-reference'])
        with self.assertRaisesRegex(IntegrationError,'configuration_schema'):
            service.configure('revision',json.dumps({'version':1,'id':'release-reference','operation':'disable'}))
        self.assertIn("value['skills']['enabled']=['explain-system']",h.USER_CLIENT)

    def test_phase_transport_ack_is_not_completion_or_replay_permission(self):
        phases=['ui-prepare','ui-en'];events=[]
        self.assertEqual(c.phase_request_error(phases,events,'ui-en'),'selected_phase_order_required')
        self.assertIsNone(c.phase_request_error(phases,events,'ui-prepare'))
        events.append({'result':{'phase_requested':'ui-prepare','native_postcondition_pending':True}})
        self.assertEqual(c.phase_request_error(phases,events,'ui-en'),'native_phase_in_progress')
        events.append({'native_result':{'phase':'ui-prepare','state':'passed'}})
        self.assertEqual(c.phase_request_error(phases,events,'ui-prepare'),'inspect_prior_phase_no_replay')
        self.assertIsNone(c.phase_request_error(phases,events,'ui-en'))
        events.extend([{'result':{'phase_requested':'ui-en'}},{'native_result':{'phase':'ui-en','state':'failed'}}])
        self.assertEqual(c.phase_request_error(phases,events,'ui-en'),'native_phase_failed_inspect_report')
    def test_branding_requires_native_upgraded_defaults_and_B11_dependencies(self):
        value=manifest();value['phases'].append('branding')
        for name,version in (('toddy-branding','0.2.0-1+toddy1'),('toddy-desktop-defaults','0.2.0-1+toddy2')):
            row=copy.deepcopy(value['packages']['toddy-assistant']);row['version']=version;row['record'].update(name=name,version=version)
            row['record_text']=json.dumps(row['record']);row['record_sha256']=hashlib.sha256(row['record_text'].encode()).hexdigest()
            value['packages'][name]=row
        h.validate_manifest(value)
        value['packages']['toddy-desktop-defaults']['version']='0.2.0-1+toddy1'
        with self.assertRaisesRegex(ValueError,'background_upgrade_required'):h.validate_manifest(value)
        status={'owner_review':{'phase_2_approved':True},'milestones':[{'id':'B11','depends_on':['B02','B06']},{'id':'B02','status':'completed'},{'id':'B06','status':'in_progress'}]}
        self.assertFalse(c.phase_eligible('branding',status))
        status['milestones'][2]['status']='completed';self.assertTrue(c.phase_eligible('branding',status))

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
            (context/'selected-phases.json').write_text(json.dumps(['ui-prepare','ui-en']))
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
                with patch.object(c,'phase_eligible',return_value=True),patch.object(c.subprocess,'check_output',return_value=''):
                    reply=c.send(context,{'request_id':'phase-first','action':'phase','phase':'ui-prepare'})
                    self.assertTrue(reply['native_postcondition_pending'])
                    reply=c.send(context,{'request_id':'phase-queued','action':'phase','phase':'ui-en'})
                    self.assertEqual(reply['error'],'native_phase_in_progress')
                self.assertEqual(c.send(context,{'request_id':'done-while-running','action':'done'}),{'error':'native_phase_in_progress'})
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

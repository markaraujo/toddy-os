"""Synthetic GSettings shim/source parser fixtures; no host/user/VM settings writes."""
import copy,hashlib,io,json,os,sys,tempfile,types,unittest
from pathlib import Path
from unittest.mock import patch
from scripts.build.phase2 import owner_setting_evidence as e


def setting(owner=None,number=1):
    owner=owner or {'username':'owner','uid':1000,'gid':1000}
    return {'schema':e.SCHEMA,'key':e.KEY,'value':True,'user_value':True,'variant_type':'b','backend':'dconf',
        'initial_value':False if number==1 else True,'initial_user_value':None if number==1 else True,'uid':owner['uid'],'gid':owner['gid'],'home':'/home/'+owner['username'],
        'operation':'set-sync-read' if number==1 else 'read-only','session_bus':'native-owner-session',
        'database':{'path':'/home/'+owner['username']+'/.config/dconf/user','sha256':'d'*64,'bytes':100,'mode':0o644,'uid':owner['uid'],'gid':owner['gid'],'nlink':1}}


def child_fixture(home,plan,number,state):
    """Executes actual marker/readback source with explicit unqualified GI shim."""
    class Variant:
        def get_type_string(self):return 'b'
        def unpack(self):return state['user_value']
    class Settings:
        @staticmethod
        def new(schema):assert schema==e.SCHEMA;return Settings()
        @staticmethod
        def sync():state['synced']=True
        def is_writable(self,key):return True
        def set_boolean(self,key,value):state['user_value']=value;state['writes']=state.get('writes',0)+1;return True
        def get_boolean(self,key):return state.get('default',False) if state.get('user_value') is None else state['user_value']
        def get_user_value(self,key):return Variant() if state.get('user_value') is not None else None
    gi=types.ModuleType('gi');gi.require_version=lambda *args:None
    repository=types.ModuleType('gi.repository');repository.Gio=types.SimpleNamespace(Settings=Settings)
    request={'uid':os.getuid(),'gid':os.getgid(),'home':str(home),'operation_id':plan['operation_id'],
        'plan_sha256':plan['plan_sha256'],'round':number,'recovery':number==3}
    env={'HOME':str(home),'XDG_CONFIG_HOME':str(home/'.config'),'GSETTINGS_BACKEND':'dconf','DBUS_SESSION_BUS_ADDRESS':'unix:path=/run/user/'+str(os.getuid())+'/bus'}
    stdout=io.StringIO()
    with patch.dict(sys.modules,{'gi':gi,'gi.repository':repository}),patch.dict(os.environ,env,clear=True),\
            patch.object(sys,'stdin',types.SimpleNamespace(buffer=io.BytesIO(json.dumps(request).encode()))),patch.object(sys,'stdout',stdout),patch.object(os,'getgroups',return_value=[]),patch.object(os,'geteuid',return_value=os.getuid()):
        exec(compile(e.OWNER_CHILD,'UNQUALIFIED-GSETTINGS-SHIM-FIXTURE','exec'),{'__name__':'__main__'})
    return json.loads(stdout.getvalue())


class OwnerSettingEvidenceTests(unittest.TestCase):
    def test_actual_marker_code_writes_once_and_round2_only_reads_with_persisted_user_value(self):
        with tempfile.TemporaryDirectory() as directory:
            home=Path(directory);db=home/'.config/dconf/user';(home/'.config').mkdir(mode=0o700);db.parent.mkdir(mode=0o700);db.write_bytes(b'unqualified-dconf-shim-fixture');db.chmod(0o600)
            plan={'operation_id':'a'*32,'plan_sha256':'b'*64};state={'user_value':None}
            first=child_fixture(home,plan,1,state);before=db.read_bytes();second=child_fixture(home,plan,2,state)
            self.assertEqual(state['writes'],1);self.assertTrue(state['synced'])
            self.assertEqual(first['marker_sha256'],second['marker_sha256']);self.assertEqual(db.read_bytes(),before)
            marker=home/('.toddy-install-proof-'+'a'*32);self.assertEqual(marker.read_bytes(),e.owner_marker('b'*64))
            with self.assertRaises(AssertionError):child_fixture(home,plan,1,state)
    def test_legitimate_owner_writable0644_database_is_recorded_without_chmod(self):
        with tempfile.TemporaryDirectory() as directory:
            home=Path(directory);db=home/'.config/dconf/user';(home/'.config').mkdir(mode=0o700);db.parent.mkdir(mode=0o700);db.write_bytes(b'unqualified-public-clock-pref-fixture');db.chmod(0o644)
            result=child_fixture(home,{'operation_id':'a'*32,'plan_sha256':'b'*64},1,{'user_value':None})
            self.assertEqual(result['setting']['database']['mode'],0o644);self.assertEqual(result['setting']['database']['nlink'],1)
            self.assertEqual(db.stat().st_mode&0o777,0o644)

    def test_global_default_or_memory_fallback_is_not_a_persisted_owner_setting(self):
        with tempfile.TemporaryDirectory() as directory:
            home=Path(directory);db=home/'.config/dconf/user';(home/'.config').mkdir(mode=0o700);db.parent.mkdir(mode=0o700);db.write_bytes(b'fixture');db.chmod(0o600)
            with self.assertRaises(AssertionError):child_fixture(home,{'operation_id':'a'*32,'plan_sha256':'b'*64},2,{'user_value':None,'default':True})
            self.assertFalse((home/('.toddy-install-proof-'+'a'*32)).exists())
    def test_readback_requires_exact_key_true_user_variant_and_protected_database(self):
        owner={'username':'owner','uid':1000,'gid':1000};self.assertEqual(e.validate_setting(setting(),owner,1)['key'],e.KEY)
        for field,value in [('value',False),('user_value',None),('backend','memory'),('uid',0),('operation','read-only')]:
            changed=setting();changed[field]=value
            with self.assertRaises(ValueError):e.validate_setting(changed,owner,1)
        changed=setting();changed['database']['mode']=0o664
        with self.assertRaisesRegex(ValueError,'protected'):e.validate_setting(changed,owner,1)
    def test_owner_child_uses_native_privilege_drop_clean_home_xdg_sessionbus_and_no_preexec(self):
        account=types.SimpleNamespace(pw_uid=1000,pw_gid=1000,pw_dir='/home/owner')
        with patch.object(e.Path,'exists',return_value=False):
            with self.assertRaisesRegex(ValueError,'graphical_owner_session_bus'):e.run_owner_state(account,{},1,False)
        with patch.object(e.Path,'exists',return_value=False),patch.object(e.subprocess,'run',return_value=types.SimpleNamespace(stdout=b'{}')) as run:
            e.run_owner_state(account,{'operation_id':'a'*32,'plan_sha256':'b'*64},3,True)
            kw=run.call_args.kwargs
            self.assertEqual((kw['user'],kw['group'],kw['extra_groups'],kw['umask']),(1000,1000,(),0o077))
            self.assertEqual(kw['env']['HOME'],'/home/owner');self.assertEqual(kw['env']['GSETTINGS_BACKEND'],'dconf')
            self.assertNotIn('preexec_fn',kw);self.assertNotIn('PYTHONPATH',kw['env'])
    def companion(self):
        owner={'username':'owner','uid':1000,'gid':1000};marker=hashlib.sha256(e.owner_marker('a'*64)).hexdigest()
        boots=[{'boot_id':str(number)*8+'-'+str(number)*4+'-'+str(number)*4+'-'+str(number)*4+'-'+str(number)*12,'root_uuid':'abcd-1234','persistent_marker_sha256':marker} for number in (1,2)]
        boot={'firmware':'bios','boots':boots}
        source={key:'c'*64 for key in ('iso_sha256','live_inputs_sha256','live_controller_sha256','cold_sha256','disk_sha256','handoff_sha256','owner_boot_inputs_sha256','observer_sha256','setting_helper_sha256')}
        source['setting_helper_sha256']=hashlib.sha256(Path(e.__file__).read_bytes()).hexdigest()
        return {'version':1,'kind':'native-owner-setting-persistence-v1','firmware':'bios','boot_receipt_sha256':'b'*64,'source':source,'expected_owner':owner,'plan_sha256':'a'*64,'rounds':[{**row,'round':number,'setting':setting(owner,number)} for number,row in enumerate(boots,1)]},boot
    def test_companion_binds_two_real_rounds_iso_source_owner_and_unchanged_runtime_rows(self):
        value,boot=self.companion();e.validate_companion(value,boot,'b'*64,iso_sha256='c'*64)
        for mutation in ('missing','wrong-iso','write-on-round2','wrong-boot','root-owner','bare-passed'):
            changed=copy.deepcopy(value)
            if mutation=='missing':changed['rounds'].pop()
            elif mutation=='wrong-iso':changed['source']['iso_sha256']='f'*64
            elif mutation=='write-on-round2':changed['rounds'][1]['setting']['operation']='set-sync-read'
            elif mutation=='wrong-boot':changed['rounds'][1]['boot_id']='3'*36
            elif mutation=='root-owner':changed['expected_owner']['uid']=0
            else:changed={'passed':True}
            with self.assertRaises(ValueError):e.validate_companion(changed,boot,'b'*64,iso_sha256='c'*64)

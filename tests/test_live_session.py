"""Live authority source fixtures; no Polkit/logind/VM/session mutation."""
import copy
import hashlib
import tempfile
import os
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

from runtime.installer.live_session import validate_attestation,authorize_live_owner,IMAGE_CLASS,active_session
from runtime.installer.disk_plan import InstallError

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('live_profile',ROOT/'scripts/build/phase2/live_profile.py')
profile=importlib.util.module_from_spec(spec);spec.loader.exec_module(profile)


class LiveSessionTests(unittest.TestCase):
    def setUp(self):
        self.boot={'boot_id':'11111111-1111-1111-1111-111111111111','image_class_sha256':'a'*64,'media_id':'b'*64,'producer_sha256':'c'*64,'unit_sha256':'d'*64}
        self.producer={'producer_pid':12345,'producer_invocation':'e'*32}
        self.value={'version':1,'uid':1000,'user':'toddy-live','session_id':'c2',**self.boot,**self.producer}
    def test_all_actual_facts_required_marker_never_sufficient(self):
        self.assertTrue(validate_attestation(self.value,self.boot,self.producer,'c2',1000))
        for changed in ({**self.boot,'boot_id':'22222222-2222-2222-2222-222222222222'},{**self.boot,'media_id':'f'*64},{**self.boot,'image_class_sha256':'f'*64}):
            with self.assertRaises(InstallError):validate_attestation(self.value,changed,self.producer,'c2',1000)
        for producer in ({**self.producer,'producer_pid':777},{**self.producer,'producer_invocation':'f'*32}):
            with self.assertRaises(InstallError):validate_attestation(self.value,self.boot,producer,'c2',1000)
        with self.assertRaises(InstallError):validate_attestation(self.value,self.boot,self.producer,'new-session',1000)
        with self.assertRaises(InstallError):validate_attestation(self.value,self.boot,self.producer,'c2',1001)
    def test_wrong_host_cannot_reach_marker_authority(self):
        with patch('runtime.installer.live_session.os.getuid',return_value=0),patch('runtime.installer.live_session.os.geteuid',return_value=0),patch('runtime.installer.live_session.boot_facts',side_effect=InstallError('installer_live_os')),patch('runtime.installer.live_session.producer_facts',side_effect=AssertionError('No unit/marker authority from foreign host')):
            with self.assertRaisesRegex(InstallError,'live_os'):authorize_live_owner(1000)
    def test_locked_remote_wrong_service_or_inactive_session_refused(self):
        fields={'User':'1000','Name':'toddy-live','Active':'yes','Remote':'no','LockedHint':'no','Type':'wayland','Class':'user','State':'active','Service':'gdm-autologin'}
        for key,value in [('LockedHint','yes'),('Remote','yes'),('Active','no'),('Service','gdm-password'),('User','1001'),('Type','x11')]:
            changed={**fields,key:value}
            with patch('runtime.installer.live_session.command',side_effect=['c2','\n'.join(k+'='+v for k,v in changed.items())]):
                with self.assertRaisesRegex(InstallError,'session_required'):active_session()
        with patch('runtime.installer.live_session.command',side_effect=['c2','\n'.join(k+'='+v for k,v in fields.items())]):self.assertEqual(active_session(),'c2')

    def test_fixed_live_rule_does_not_grant_generic_executor_or_acquisition(self):
        self.assertIn('io.github.markaraujo.Toddy.Install',profile.RULE_TEXT)
        self.assertIn('action.lookup("program") === "/usr/libexec/toddy-installer-auth"',profile.RULE_TEXT)
        self.assertIn('subject.local === true && subject.active === true',profile.RULE_TEXT)
        self.assertNotIn('AcquireNative',profile.RULE_TEXT);self.assertNotIn('Executor',profile.RULE_TEXT)
        self.assertNotIn('exec.allow_gui',profile.RULE_TEXT)
    def test_fresh_account_never_inherits_builder_or_wheel_membership(self):
        base={'passwd':b'root:x:0:0:root:/root:/bin/bash\n','group':b'root:x:0:\nwheel:x:97:\n',
              'shadow':b'root:!:::::::\n','gshadow':b'root:!::\nwheel:!::\n'}
        result=profile.account_transform(base)
        self.assertIn(b'toddy-live:x:1000:1000:',result['passwd'])
        self.assertIn(b'toddy-live:!:::::::',result['shadow'])
        self.assertIn(b'wheel:x:97:\n',result['group']);self.assertNotIn(b'wheel:x:97:toddy-live',result['group'])
        with self.assertRaisesRegex(ValueError,'collision'):profile.account_transform(result)
        inherited={**base,'passwd':base['passwd']+b'builder:x:1001:1001:Builder:/home/builder:/bin/bash\n'}
        with self.assertRaisesRegex(ValueError,'inherited'):profile.account_transform(inherited)
    def test_media_identity_not_self_referential_to_final_image(self):
        first=profile.media_identity('a'*64,'b'*64)
        self.assertEqual(first,profile.media_identity('a'*64,'b'*64))
        self.assertNotEqual(first,profile.media_identity('c'*64,'b'*64))
        self.assertEqual(IMAGE_CLASS,Path('/usr/share/toddy/live-image.json'))


class LiveProfilePlanTests(unittest.TestCase):
    def test_plan_is_fresh_live_only_and_never_bakes_runtime_authority(self):
        from runtime.installer.native_finalizer import payload_module
        p=payload_module()
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);entries={}
            def add(virtual,data):
                path=root/virtual.lstrip('/');path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
                entries[virtual]={'sha256':hashlib.sha256(data).hexdigest()}
            for virtual in (profile.PRODUCER,'/usr/bin/dconf','/usr/bin/loginctl','/usr/bin/systemctl','/usr/lib/security/pam_exec.so','/usr/lib/security/pam_succeed_if.so','/usr/share/wayland-sessions/gnome.desktop'):add(virtual,b'synthetic source plan fixture')
            for schema,key,kind in [('lockdown','disable-lock-screen','b'),('screensaver','lock-enabled','b'),('session','idle-delay','u')]:
                add('/usr/share/glib-2.0/schemas/org.gnome.desktop.'+schema+'.gschema.xml',('<schemalist><schema id="org.gnome.desktop.'+schema+'"><key name="'+key+'" type="'+kind+'"/></schema></schemalist>').encode())
            add('/etc/gdm/custom.conf',b'[daemon]\nAutomaticLoginEnable=false\n')
            add('/etc/pam.d/gdm-autologin',b'auth required pam_succeed_if.so uid >= 1000 quiet\naccount  include        system-account\nsession  include        system-session\n')
            for name,data in {'passwd':b'root:x:0:0:root:/root:/bin/bash\n','group':b'root:x:0:\nwheel:x:97:\n','shadow':b'root:!:::::::\n','gshadow':b'root:!::\nwheel:!::\n'}.items():add('/etc/'+name,data)
            manifest={'ownership':{'entries':entries},'components':[{'name':name,'version':version+'-1+toddy1'} for name,version in [('gdm','50.2'),('dconf','0.49.0'),('gsettings-desktop-schemas','50.1')]]}
            media=profile.media_identity(hashlib.sha256(p.encoded(manifest)).hexdigest(),'a'*64)
            files,links,image=profile.plan(root,manifest,media,'a'*64)
            self.assertFalse(any(path.startswith('/run/') for path in files))
            self.assertIn(b'AutomaticLogin = toddy-live',files['/etc/gdm/custom.conf'][0])
            self.assertIn(b'pam_exec.so quiet /usr/libexec/toddy-live-session pam',files['/etc/pam.d/gdm-autologin'][0])
            self.assertEqual(image['live_uid'],1000);self.assertEqual(image['media_id'],media)
            self.assertEqual((root/'etc/gdm/custom.conf').read_bytes(),b'[daemon]\nAutomaticLoginEnable=false\n')
            with self.assertRaisesRegex(ValueError,'media identity'):profile.plan(root,manifest,'f'*64,'a'*64)
    def test_live_stage_cannot_operate_arbitrary_path_before_any_fact_or_write(self):
        class Assembly:
            root=Path('/synthetic/root');work=Path('/synthetic')
            def recheck(self):pass
        class System:
            def require_root(self):pass
            def run(self,*args,**kwargs):raise AssertionError('No native command')
        with self.assertRaisesRegex(ValueError,'fixed reviewed'):profile.stage(Assembly(),{}, {},'a'*64,System())

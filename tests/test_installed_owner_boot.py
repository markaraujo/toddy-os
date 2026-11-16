"""Synthetic native observation fixtures; never actual boot/login acceptance."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import subprocess
from types import SimpleNamespace
import unittest
from unittest.mock import Mock,patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts/host'))
import installed_owner_boot as control
SPEC=importlib.util.spec_from_file_location('installed_probe',ROOT/'scripts/host/installed-owner-probe.py')
probe=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(probe)


def handoff():
    return {'version':1,'kind':'native-installed-disk-handoff-v1','state':'completed-install-detached-boots-pending',
        'firmware':'bios','target_serial':'TODDY-INSTALL-P2-1','operation_id':'a'*32,'production_ready':False,'detached_boots_collected':0,
        'expected_owner':{'username':'owner','uid':1000,'gid':1000},'root_uuid':'abcd-1234',
        **{name:'b'*64 for name in ('plan_sha256','input_manifest_sha256','image_manifest_sha256','kernel_sha256','initramfs_sha256','initramfs_source_sha256','grub_config_sha256')}}


class InstalledControlTests(unittest.TestCase):
    def test_only_installed_overlay_and_firmware_drives_no_live_or_build_disks(self):
        for firmware in ('bios','uefi'):
            for number in (1,2,3):
                value={**handoff(),'firmware':firmware};args=control.qemu(value,number,number==3)
                drives=[args[i+1] for i,item in enumerate(args) if item=='-drive']
                self.assertEqual(len(drives),1 if firmware=='bios' else 3)
                self.assertEqual(drives[0],'file=/work/target.qcow2,if=none,id=root,format=qcow2,bps_wr=16777216')
                self.assertEqual(args[args.index('-nic')+1],'none');self.assertNotIn('-kernel',args);self.assertNotIn('-cdrom',args)
                self.assertNotIn('-append',args);self.assertNotIn('-snapshot',args)
                self.assertIn('file:/work/observation-'+str(number)+'.log',args)
                self.assertIn('unix:/work/q-'+str(number)+',server=on,wait=off',args)
                self.assertEqual(sum('credential.binary:toddy.boot-probe=' in item for item in args),1)

    def test_real_observation_required_and_recovery_cannot_count_as_normal_boot(self):
        value=handoff();row={'boot_id':'11111111-1111-1111-1111-111111111111','root_uuid':value['root_uuid'],
            'persistent_marker_sha256':hashlib.sha256(control.owner_evidence.owner_marker(value['plan_sha256'])).hexdigest(),
            'kernel_release':'7.1.8-toddy','installer_media_attached':False,'fresh_owner_login':True,'initramfs_sha256':'b'*64,
            'session_type':'wayland','round':1,'recovery':False,'observer_only_extra_write':'explicit-owner-file-marker-and-clock-preference','owner_setting':__import__('tests.test_owner_setting_evidence',fromlist=['setting']).setting()}
        encode=lambda data:'TODDY_INSTALLED_OWNER '+json.dumps({'state':'observed','observation':data})+'\n'
        self.assertEqual(control.parse_observation(encode(row),value,1,False),row)
        for changed in ({'fresh_owner_login':False},{'installer_media_attached':True},{'session_type':'tty'},{'root_uuid':'beef-1234'},
                {'recovery':True},{'persistent_marker_sha256':'f'*64}):
            with self.assertRaises(ValueError):control.parse_observation(encode({**row,**changed}),value,1,False)
        with self.assertRaises(ValueError):control.parse_observation('QMP success only\n',value,1,False)
        with self.assertRaises(ValueError):control.parse_observation(encode(row)*2,value,1,False)

    def test_handoff_requires_fresh_actual_owner_and_fixed_install_serial(self):
        self.assertEqual(control.validate_handoff(handoff()),handoff())
        for changed in ({'target_serial':'TODDY-LFS-TARGET'},{'production_ready':True},{'operation_id':'new'},
                {'expected_owner':{'username':'root','uid':0,'gid':0}},{'expected_owner':None},{'root_uuid':None}):
            with self.assertRaises(ValueError):control.validate_handoff({**handoff(),**changed})
        self.assertEqual(control.key_codes('_'),['shift','minus'])
        with self.assertRaises(ValueError):control.key_codes('\n')

    def test_measured_capacity_preserves_absolute_floor_and_stop_margin(self):
        allocated=3*1024**3
        minimum=control.HOST_FLOOR+allocated+2*1024**3
        self.assertTrue(control.capacity_admitted(minimum,allocated))
        self.assertFalse(control.capacity_admitted(minimum-1,allocated))
        self.assertTrue(control.capacity_stop_required(control.HOST_FLOOR+control.STOP_HEADROOM-1))
        self.assertFalse(control.capacity_stop_required(control.HOST_FLOOR+control.STOP_HEADROOM))
        self.assertGreater(control.STOP_HEADROOM,control.WRITE_BPS*20*2)

    def test_low_space_requests_only_owned_powerdown_and_never_accepts_boot(self):
        with tempfile.TemporaryDirectory() as temporary:
            context=Path(temporary);process=Mock();process.poll.return_value=None
            with patch.object(control.subprocess,'Popen',return_value=process),patch('shutil.disk_usage',return_value=SimpleNamespace(free=control.HOST_FLOOR)),\
                    patch.object(control,'powerdown_owned') as powerdown:
                with self.assertRaisesRegex(ValueError,'capacity_stop_uncertain'):control.wait_owned('fixture-cid','fixture-run',context,1)
                powerdown.assert_called_once_with('fixture-cid','fixture-run',context/'q-1')
                report=json.loads((context/'capacity-stop-1.json').read_bytes());self.assertFalse(report['boot_accepted'])
                process.terminate.assert_called_once();self.assertFalse((context/'round-1.json').exists())

    def test_isolated_direct_entry_help_imports_without_native_commands(self):
        result=subprocess.run([sys.executable,'-I',str(ROOT/'scripts/host/installed_owner_boot.py'),'--help'],capture_output=True,text=True,timeout=10)
        self.assertEqual(result.returncode,0,result.stderr);self.assertIn('--context',result.stdout)

    def test_explicit_stop_checks_exact_vm_and_cannot_count_as_boot(self):
        with tempfile.TemporaryDirectory() as temporary:
            context=Path(temporary);value=handoff()
            (context/'handoff.json').write_text(json.dumps(value));(context/'active.json').write_text(json.dumps({'container_id':'fixture-cid','run_id':'fixture-run','round':1}))
            inspection={'Config':{'Labels':{'toddy.boot-test':'fixture-run'},'Cmd':control.qemu(value,1,False)},'State':{'Running':True},
                'Mounts':[{'Type':'bind','Source':str(control.SOURCE),'Destination':'/installed/source.qcow2','RW':False},
                    {'Type':'bind','Source':str(context),'Destination':'/work','RW':True}], 'HostConfig':{'NetworkMode':'none'}}
            with patch.object(control.subprocess,'check_output',side_effect=lambda *a,**kw:json.dumps([inspection])),patch.object(control,'powerdown_owned') as powerdown,\
                    patch.object(control.subprocess,'run'),patch.object(control.boot,'stop_owned_container',return_value={'Running':False}) as stop:
                self.assertEqual(control.qmp(context,'stop'),{'stopped':True,'boot_accepted':False})
                powerdown.assert_called_once_with('fixture-cid','fixture-run',context/'q-1');stop.assert_called_once_with('fixture-cid','fixture-run')
                self.assertFalse(json.loads((context/'operator-stop-1.json').read_bytes())['boot_accepted'])
                inspection['Mounts'][0]['RW']=True
                with self.assertRaisesRegex(ValueError,'owned_running'):control.qmp(context,'stop')
                self.assertEqual(stop.call_count,1)

    def test_private_source_rejects_symlinks_hardlinks_and_writable_modes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);file=root/'disk';file.write_bytes(b'fixture');file.chmod(0o600)
            self.assertEqual(control.private(file),file)
            os.link(file,root/'other')
            with self.assertRaises(ValueError):control.private(file)
            (root/'other').unlink();file.chmod(0o644)
            with self.assertRaises(ValueError):control.private(file)
            file.chmod(0o600);(root/'link').symlink_to(file)
            with self.assertRaises(ValueError):control.private(root/'link')


class OwnerProbeTests(unittest.TestCase):
    def test_fixture_real_marker_creation_and_second_read_only_persistence(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);home=root/'home/owner';home.mkdir(parents=True);home.chmod(0o700)
            expected=handoff();expected['expected_owner'].update(uid=os.getuid(),gid=os.getgid())
            fixtures={'/boot/vmlinuz-7.1.8-toddy':b'kernel','/boot/initramfs-7.1.8-toddy-installed.img':b'initramfs','/etc/toddy/grub.cfg':b'grub',
                '/proc/cmdline':b'root=UUID=abcd-1234','/proc/sys/kernel/random/boot_id':b'11111111-1111-1111-1111-111111111111'}
            for path,data in fixtures.items():
                target=root/path.lstrip('/');target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
            for key,path in [('kernel_sha256','/boot/vmlinuz-7.1.8-toddy'),('initramfs_sha256','/boot/initramfs-7.1.8-toddy-installed.img'),('grub_config_sha256','/etc/toddy/grub.cfg')]:
                expected[key]=hashlib.sha256(fixtures[path]).hexdigest()
            def command(argv):
                if 'findmnt' in argv[0]:return json.dumps({'filesystems':[{'target':'/','source':'/dev/vda2','fstype':'ext4','uuid':'abcd-1234'}]})
                if 'lsblk' in argv[0]:return json.dumps({'blockdevices':[{'type':'disk','serial':'TODDY-INSTALL-P2-1'}]})
                if 'list-sessions' in argv:return '2 owner'
                if 'show-session' in argv:return f'User={os.getuid()}\nName=owner\nActive=yes\nRemote=no\nType=wayland\nClass=user\nService=gdm-password'
                if 'is-active' in argv:return 'active'
                raise AssertionError(argv)
            account=SimpleNamespace(pw_uid=os.getuid(),pw_gid=os.getgid(),pw_dir='/home/owner')
            from tests.test_owner_setting_evidence import child_fixture
            db=home/'.config/dconf/user';(home/'.config').mkdir(mode=0o700);db.parent.mkdir(mode=0o700);db.write_bytes(b'unqualified-dconf-shim-fixture');db.chmod(0o600)
            state={'user_value':None}
            def owner_state(account,plan,number,recovery):return child_fixture(home,plan,number,state)
            with patch.object(probe,'Path',side_effect=lambda path:Path(path) if Path(path).is_relative_to(root) else root/str(path).lstrip('/')),patch.object(probe,'command',side_effect=command),\
                    patch.object(probe,'run_owner_state',side_effect=owner_state),patch.object(probe.pwd,'getpwnam',return_value=account),patch.object(probe.os,'geteuid',return_value=0),\
                    patch.object(probe.os,'uname',return_value=SimpleNamespace(release='7.1.8-toddy')),patch.object(probe.os,'setgroups'),\
                    patch.object(probe.os,'setgid'),patch.object(probe.os,'setuid'),patch.object(probe.subprocess,'run',return_value=SimpleNamespace(returncode=0)):
                first=probe.observe(expected,1);second=probe.observe(expected,2)
                self.assertEqual(first['persistent_marker_sha256'],second['persistent_marker_sha256'])
                marker=home/('.toddy-install-proof-'+'a'*32)
                self.assertEqual(marker.read_bytes(),control.owner_evidence.owner_marker('b'*64));self.assertEqual(marker.stat().st_mode&0o777,0o600)
                # Existing marker cannot be overwritten by replaying round 1.
                with self.assertRaises(AssertionError):probe.observe(expected,1)
                # An active autologin session is not fresh authenticated owner proof.
                with patch.object(probe,'command',side_effect=lambda argv:command(argv).replace('gdm-password','gdm-autologin')),patch.object(probe.time,'monotonic',side_effect=[0,0,1000]),patch.object(probe.time,'sleep'):
                    with self.assertRaisesRegex(AssertionError,'fresh owner login'):probe.observe(expected,2)
                self.assertEqual(marker.read_bytes(),control.owner_evidence.owner_marker('b'*64))

if __name__=='__main__':unittest.main()

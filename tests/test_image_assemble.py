"""Archive assembly guards and exact native command fixtures, never guest proof."""
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

SOURCE=Path(__file__).resolve().parents[1]/'scripts/build/phase2/image_assemble.py'
spec=importlib.util.spec_from_file_location('image_assemble',SOURCE)
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)


def root_fixture_lstat(path, *args, **kwargs):
    info=ORIGINAL_LSTAT(path,*args,**kwargs)
    values=list(info);values[4]=values[5]=0;values[2]=Path('/').stat().st_dev
    return os.stat_result(values)


ORIGINAL_LSTAT=Path.lstat


class AssemblyTests(unittest.TestCase):
    def test_host_root_guard_fails_before_native_package_command(self):
        system=Mock()
        with self.assertRaises((ValueError,FileNotFoundError)):
            a.native_guard(system)
        system.run.assert_not_called()

    def test_no_existing_or_uncertain_root_can_be_reused(self):
        with tempfile.TemporaryDirectory() as temporary:
            stage=Path(temporary);stage.chmod(0o755)
            (stage/'toddy-offline-image-1').mkdir()
            with patch.object(a,'STAGE',stage),patch.object(Path,'lstat',root_fixture_lstat):
                with self.assertRaisesRegex(ValueError,'Preserve existing'):
                    a.AssemblyRoot('base',{'components':[{'installed_bytes':1}]})

    def test_capacity_has_floor_and_never_creates_root_when_insufficient(self):
        with tempfile.TemporaryDirectory() as temporary:
            stage=Path(temporary);stage.chmod(0o755)
            with patch.object(a,'STAGE',stage),patch.object(Path,'lstat',root_fixture_lstat),patch.object(a.os,'statvfs',return_value=Mock(f_bavail=1,f_frsize=4096)):
                with self.assertRaisesRegex(ValueError,'capacity requires'):
                    a.AssemblyRoot('base',{'components':[{'installed_bytes':1000}]})
            self.assertEqual(list(stage.iterdir()),[])

    def test_exact_commands_private_log_and_input_recheck(self):
        with tempfile.TemporaryDirectory() as temporary:
            work=Path(temporary);root=work/'root';root.mkdir();bundle=work/'bundle'
            manifest={'components':[{'name':'fixture','version':'1','architecture':'all','archive':'fixture_1_all.deb'}],
                'ownership':{'entries':{'/usr/bin/dpkg':{'sha256':'a'*64},'/usr/bin/dpkg-query':{'sha256':'a'*64}}}}
            prepared=Mock();prepared._load.return_value=manifest
            p=Mock();p.PreparedPayload.return_value=prepared;p.digest.return_value='a'*64
            assembly=Mock(root=root,work=work,required=1000,pin=(1,2,3))
            system=Mock()
            def run(command,**kwargs):
                if command[0]=='/usr/bin/dpkg-query':return 'fixture\t1\tall\tinstall ok installed'
                return ''
            system.run.side_effect=run
            with patch.object(a,'payload_module',return_value=p),patch.object(a,'bundle_namespace'),patch.object(a,'secured',side_effect=lambda x:x),patch.object(a,'write') as write:
                result=a.unpack_native(bundle,'b'*64,assembly,system)
            self.assertEqual(result['state'],'native-archives-unpacked-needs-resource-qualification')
            commands=[x.args[0] for x in system.run.call_args_list]
            self.assertEqual(commands[0],['/usr/bin/dpkg','--root='+str(root),'--log='+str(work/'dpkg.log'),'--unpack',str(bundle/'archives/fixture_1_all.deb')])
            self.assertTrue(all('--log='+str(work/'dpkg.log') in command for command in commands if command[0]=='/usr/bin/dpkg'))
            self.assertEqual(prepared._load.call_count,2)
            self.assertFalse(result['production_ready']);self.assertEqual(write.call_count,2)

    def test_adopt_completed_unpacked_root_queries_only_and_rejects_changed_pin(self):
        with tempfile.TemporaryDirectory() as temporary:
            stage=Path(temporary);work=stage/'toddy-offline-image-1';(work/'root').mkdir(parents=True)
            (work/'dpkg.log').write_text('fixture native log')
            receipt={'manifest_sha256':'a'*64,'root':str(work/'root'),'assembly_pin':[1,2,3],
                'required_bytes':a.RESERVE+1,'state':'unpack-intended'}
            (work/'unpack-intent.json').write_text(json.dumps(receipt))
            completed={**receipt,'state':'native-archives-unpacked-needs-resource-qualification',
                'dpkg_log_sha256':a.payload_module().digest(work/'dpkg.log')}
            (work/'unpacked.json').write_text(json.dumps(completed))
            manifest={'components':[{'name':'fixture','version':'1','architecture':'all'}]}
            system=Mock();system.run.return_value='fixture\t1\tall\tinstall ok installed'
            with patch.object(a,'STAGE',stage),patch.object(a,'secured',side_effect=lambda x:x),patch.object(a.AssemblyRoot,'identity',return_value=(1,2,3)):
                adopted=a.adopt_unpacked('base',manifest,'a'*64,system)
                self.assertEqual(adopted.pin,(1,2,3));self.assertEqual(system.run.call_count,1)
                self.assertEqual(system.run.call_args.args[0][0],'/usr/bin/dpkg-query')
                completed['assembly_pin']=[9,2,3];(work/'unpacked.json').write_text(json.dumps(completed))
                with self.assertRaisesRegex(ValueError,'custody'):
                    a.adopt_unpacked('base',manifest,'a'*64,system)
                self.assertEqual(system.run.call_count,1)

    def test_partial_unpack_stops_without_configure_or_success_receipt(self):
        with tempfile.TemporaryDirectory() as temporary:
            work=Path(temporary);root=work/'root';root.mkdir()
            manifest={'components':[{'archive':'fixture.deb'}],'ownership':{'entries':{'/usr/bin/dpkg':{'sha256':'a'*64},'/usr/bin/dpkg-query':{'sha256':'a'*64}}}}
            p=Mock();p.PreparedPayload.return_value._load.return_value=manifest;p.digest.return_value='a'*64
            assembly=Mock(root=root,work=work,required=1000,pin=(1,2,3));system=Mock();system.run.side_effect=RuntimeError('fixture interrupted native unpack')
            with patch.object(a,'payload_module',return_value=p),patch.object(a,'bundle_namespace'),patch.object(a,'secured',side_effect=lambda x:x),patch.object(a,'write') as write:
                with self.assertRaises(RuntimeError):a.unpack_native(work/'bundle','b'*64,assembly,system)
            self.assertEqual(system.run.call_count,1);self.assertEqual(write.call_count,1)


if __name__=='__main__':unittest.main()

"""B12 media binding fixtures; no native compression/boot execution."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock,patch

SOURCE=Path(__file__).resolve().parents[1]/'scripts/build/phase2/image_media.py'
spec=importlib.util.spec_from_file_location('image_media',SOURCE)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


class MediaTests(unittest.TestCase):
    def test_missing_final_assembly_stops_before_native_tools_or_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            with patch.object(m,'JOURNAL',Path(temporary)/'absent'),patch.object(m.initramfs_input,'physical',side_effect=lambda root,path,**kwargs:path),patch.object(m,'native_tools') as native:
                with self.assertRaises(FileNotFoundError):m.compression_phase(Mock())
                native.assert_not_called()

    def test_assembly_requires_actual_snapshot_current_producer_and_exact_action(self):
        with tempfile.TemporaryDirectory() as temporary:
            work=Path(temporary);image=work/'root';image.mkdir();evidence=work/'evidence';evidence.mkdir()
            assembler=work/'producer.py';assembler.write_text('# actual source fixture\n')
            expected={'entries':{},'hardlink_groups':[]}
            manifest=evidence/'image.json';manifest.write_text(json.dumps(expected))
            journal={'assembled':True,'release_profile':True,'image':str(image),'evidence':str(evidence),
                'assembler_sha256':m.p.digest(assembler),'actions':[{'step':'image-manifest','finished':True,'report':'image.json','sha256':m.p.digest(manifest)}]}
            path=evidence/'assembly.json';path.write_text(json.dumps(journal))
            with patch.object(m,'JOURNAL',path),patch.object(m,'IMAGE',image),patch.object(m,'ASSEMBLER',assembler),patch.object(m.initramfs_input,'physical',side_effect=lambda root,path,**kwargs:path),patch.object(m,'snapshot',return_value=expected),patch.object(m,'tree_names',return_value=['.']):
                self.assertEqual(m.assembly_input()[2],expected)
                journal['actions'].append(journal['actions'][0]);path.write_text(json.dumps(journal))
                with self.assertRaisesRegex(ValueError,'manifest action'):m.assembly_input()
                journal['actions'].pop();path.write_text(json.dumps(journal));assembler.write_text('changed')
                with self.assertRaisesRegex(ValueError,'current B12'):m.assembly_input()

    def test_native_tool_versions_and_record_hashes_come_from_current_projection(self):
        with tempfile.TemporaryDirectory() as temporary:
            path=Path(temporary)/'projection.json'
            rows=[{'name':name,'version':'1','component_record_sha256':'a'*64,'archive_sha256':'b'*64} for name in m.TOOLS]
            path.write_text(json.dumps({'components':rows}))
            evidence={name:{'record_sha256':'a'*64,'archive_sha256':'b'*64} for name in m.TOOLS}
            with patch.object(m,'PROJECTION',path),patch.object(m.initramfs_input,'physical',side_effect=lambda root,path,**kwargs:path),patch.object(m.assemble_iso,'packages',return_value=(evidence,{})) as native:
                versions,_,_=m.native_tools(Mock())
                self.assertEqual(versions,{name:'1' for name in m.TOOLS})
                self.assertEqual(native.call_args.args[1],versions)
                evidence['linux-kernel']['record_sha256']='c'*64
                with self.assertRaisesRegex(ValueError,'differ'):m.native_tools(Mock())

    def test_capacity_preserves16gib_floor_in_addition_to_all_readbacks(self):
        with patch.object(m.os,'statvfs',return_value=Mock(f_bavail=16*1024**3,f_frsize=1)):
            with self.assertRaisesRegex(ValueError,'reserve'):m.capacity(Path('/fixture'),1)
        with patch.object(m.os,'statvfs',return_value=Mock(f_bavail=16*1024**3+100,f_frsize=1)):
            m.capacity(Path('/fixture'),100)

    def test_live_identity_comes_from_precompression_payload_policy_and_owned_class(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);image=root/'image';stage=root/'stage';here=root/'code';here.mkdir()
            files={image/'usr/lib/toddy/installer/live_session.py':b'producer',
                image/'etc/systemd/system/toddy-live-owner.service':b'unit',here/'live_profile.py':b'profile',
                stage/'toddy-live-native-inputs/payload/manifest.json':b'payload',
                stage/'toddy-live-native-inputs/policy.json':b'policy'}
            for path,data in files.items():path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
            media='a'*64
            value={'version':1,'image_class':'phase2-live-installer','live_uid':1000,'live_user':'toddy-live',
                'media_id':media,'producer_sha256':m.p.digest(image/'usr/lib/toddy/installer/live_session.py'),
                'unit_sha256':m.p.digest(image/'etc/systemd/system/toddy-live-owner.service'),
                'profile_source_sha256':m.p.digest(here/'live_profile.py')}
            path=image/'usr/share/toddy/live-image.json';path.parent.mkdir(parents=True);path.write_text(json.dumps(value))
            helper=Mock();helper.media_identity.return_value=media
            with patch.dict('sys.modules',{'live_profile':helper}),patch.object(m,'IMAGE',image),patch.object(m,'STAGE',stage),patch.object(m,'HERE',here),patch.object(m.initramfs_input,'physical',side_effect=lambda root,path,**kwargs:path):
                self.assertEqual(m.live_identity(),media)
                helper.media_identity.assert_called_with(m.p.digest(stage/'toddy-live-native-inputs/payload/manifest.json'),m.p.digest(stage/'toddy-live-native-inputs/policy.json'))
                value['media_id']='b'*64;path.write_text(json.dumps(value))
                with self.assertRaisesRegex(ValueError,'media identity differs'):m.live_identity()
                value['media_id']=media;value['producer_sha256']='c'*64;path.write_text(json.dumps(value))
                with self.assertRaisesRegex(ValueError,'source/unit custody'):m.live_identity()

    def test_initramfs_cannot_reuse_other_compression_generation(self):
        with tempfile.TemporaryDirectory() as temporary:
            work=Path(temporary);(work/'manifest.json').write_text(json.dumps({'compression_binding':{'fixture':'old'}}))
            with patch.object(m,'INITRAMFS',work),patch.object(m.initramfs_input,'physical',side_effect=lambda root,path,**kwargs:path),patch.object(m.initramfs_input,'verify',return_value={'fixture':'new'}):
                with self.assertRaisesRegex(ValueError,'current native root'):m.archive_input()


if __name__=='__main__':unittest.main()

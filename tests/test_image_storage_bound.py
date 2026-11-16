"""Storage-bound and dispatch-gap fixtures; no native image/VM execution."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch,Mock

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts/build/phase2')]
import offline_payload as p
import image_assemble as a
import image_media as media

POLICY={'accounts':{'passwd':'root:x:0:0:root:/root:/bin/bash\n','group':'root:x:0:\nwheel:x:97:\n'},'required_policy_paths':['/etc/pam.d/login']}


class ImageStorageTests(unittest.TestCase):
    def test_small_files_and_actual_names_cost_more_than_logical_bytes(self):
        members={'/data':{'kind':'directory'}}
        members.update({'/data/file'+str(index):{'kind':'regular','bytes':1,'hardlink_class':'/data/file'+str(index)} for index in range(2000)})
        row={'members':members,'control_bytes':12,'control_files':1,'list_bytes':100,'conffile_lines':0}
        measured=p.storage_measurements({'fixture':row},{'fresh_directories':{}},4096)
        self.assertEqual(measured['logical_regular_path_bytes'],2000)
        self.assertEqual(measured['regular_inodes'],2000)
        self.assertGreaterEqual(measured['rounded_file_data_bytes'],2000*4096)
        self.assertGreater(measured['namespace_storage_bound_bytes'],2000*4096)
        self.assertGreater(p.file_tree_storage_bound({'archives/'+('a'*100+str(index)):1 for index in range(1000)},4096),1000*4096)

    def test_root_budget_requires_measurements_and_counts_actual_policy_and_embedded_inputs(self):
        manifest={'bytes':3,'storage':{'version':1,'block_bytes':4096,'root_storage_bound_bytes':50000,'logical_regular_path_bytes':3}}
        with tempfile.TemporaryDirectory() as temporary:
            stage=Path(temporary);bundle=stage/'toddy-installer-native-inputs/payload';bundle.mkdir(parents=True)
            (bundle/'manifest.json').write_text('explicit fixture, not a signed bundle')
            (bundle/'fixture.deb').write_bytes(b'x'*10000)
            with patch.object(a,'STAGE',stage),patch.object(a,'policy_input',return_value=POLICY),patch.object(a,'secured',side_effect=lambda path,**kwargs:path),patch.object(a,'payload_module',return_value=p),patch.object(p,'PreparedPayload',return_value=Mock(_load=Mock(return_value={'fixture':'not qualification'}))),patch.object(a,'bundle_namespace'):
                base=a.root_storage_budget('base',manifest,4096)
                live=a.root_storage_budget('live',manifest,4096)
                self.assertGreater(base['fresh_account_bound_bytes'],0)
                self.assertGreater(live['embedded_offline_input_bound_bytes'],10000)
                self.assertGreater(live['root_bound_bytes'],base['root_bound_bytes'])
                self.assertTrue(live['future_qualification_artifacts_require_separate_pre_copy_measurement'])
                with self.assertRaisesRegex(ValueError,'measurements required'):a.root_storage_budget('base',{'bytes':3},4096)
                with self.assertRaisesRegex(ValueError,'measurements required'):a.root_storage_budget('base',manifest,8192)

    def test_expanded_snapshot_uses_hardlink_classes_and_rounding(self):
        snapshot={'entries':{'.':{'directory':True,'xattrs':{}},'file':{'size':1,'xattrs':{}},
            'alias':{'size':1,'xattrs':{}},'separate':{'size':1,'xattrs':{}}},'hardlink_groups':[['alias','file']]}
        with tempfile.TemporaryDirectory() as temporary:
            bound=media.expanded_snapshot_bound(Path(temporary),snapshot,4096)
            self.assertGreater(bound,3)
            independent={**snapshot,'hardlink_groups':[]}
            self.assertGreater(media.expanded_snapshot_bound(Path(temporary),independent,4096),bound)

    def test_early_runtime_budget_counts_stage_newc_and_gzip_before_copy(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);source=root/'fixture';source.write_bytes(b'clearly labelled source capacity fixture')
            runtime=Mock(PROGRAMS=('/usr/bin/fixture',),ALIASES={'bin':'usr/bin'})
            runtime.installed_records.return_value={'/usr/bin/fixture':('fixture','1','archive',{'sha256':p.digest(source)})}
            runtime.runtime_dependencies.return_value=set();runtime.target_resolve.return_value=(source,'/usr/bin/fixture')
            runtime.destination_path.side_effect=lambda path:path.lstrip('/')
            with patch.object(media.initramfs_archive,'runtime',runtime),patch.object(media,'TARGET',root),patch.object(media,'STAGE',root):
                measured=media.early_runtime_storage_bound()
                self.assertGreater(measured['source_file_bytes'],len(source.read_bytes()))
                self.assertEqual(measured['phase_bound_bytes'],measured['runtime_stage_bound_bytes']+p.rounded(measured['newc_bound_bytes'],4096)+p.rounded(measured['gzip_bound_bytes'],4096)+measured['report_metadata_bound_bytes'])
                self.assertGreater(measured['gzip_bound_bytes'],measured['newc_bound_bytes'])
                self.assertEqual(list(root.iterdir()),[source])

    def test_dispatch_guard_matches_only_real_qualified_job_schema(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory=Path(temporary)
            (directory/'custom.job.json').write_text(json.dumps({'pid':1,'command':['not-a-job.py-harness']}))
            (directory/'custom-bad.job.json').write_text('legacy custom report')
            row={'pid':123,'boot_id':'fixture','proc_start_ticks':'1','started_unix':1,
                'harness_sha256':'a'*64,'command':['/bin/bash','/opt/toddy-build/scripts/build/phase2/isolated.sh',
                    '/mnt/lfs/sources/phase2/inputs/fixture','/mnt/lfs/sources/phase2/work/fixture','bash','/src/build.sh']}
            (directory/'fixture-build.job.json').write_text(json.dumps(row))
            self.assertEqual(a.unclosed_compiler_jobs(directory),['fixture-build'])
            (directory/'fixture-build.exit').write_text('1\n')
            self.assertEqual(a.unclosed_compiler_jobs(directory),[])
            row['command']=['/bin/bash',[],None,None,None,None]
            (directory/'structured-custom.job.json').write_text(json.dumps(row))
            self.assertEqual(a.unclosed_compiler_jobs(directory),[])


if __name__=='__main__':unittest.main()

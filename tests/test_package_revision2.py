"""Revision source/refusal checks; no second archive/native install/proof created."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('package_revision2',ROOT/'scripts/build/phase2/package_revision2.py')
revision=importlib.util.module_from_spec(spec);spec.loader.exec_module(revision)


class NativeRevisionTests(unittest.TestCase):
    def test_only_control_version_changes_dependencies_and_other_fields_exact(self):
        original=b'Package: toddy-agent\nVersion: 0.2.0-1+toddy1\nArchitecture: all\nDepends: nodejs, python (>= 3.14)\nDescription: Frozen source payload\n legal continuation\n'
        result=revision.version_control(original,'0.2.0-1+toddy2')
        self.assertEqual(result,original.replace(b'Version: 0.2.0-1+toddy1',b'Version: 0.2.0-1+toddy2'))
    def test_cannot_turn_new_upstream_or_old_revision_into_lifecycle_proof(self):
        for value in ('0.3.0-1+toddy2','0.2.0-1+toddy1','0.2.0-1+toddy0','0.2.0-2','; bad'):
            with self.assertRaises(ValueError):revision.revision_version('0.2.0-1+toddy1',value)
    def test_ambiguous_control_is_refused(self):
        for data in (b'Package: toddy-agent\nVersion: 0.2.0-1+toddy1\nversion: other\n',b'Package: toddy-agent\nVersion: 0.2.0-1+toddy1\n continued\n'):
            with self.assertRaises(ValueError):revision.version_control(data,'0.2.0-1+toddy2')
    def test_host_or_other_source_location_never_builds_native_archive(self):
        with self.assertRaisesRegex(ValueError,'Designated native builder'):
            with revision.build_guard():self.fail('No actual native build')
    def test_old_installed_true_or_arbitrary_built_record_cannot_publish_revision_metadata(self):
        with tempfile.TemporaryDirectory() as temporary:
            path=Path(temporary)/'record.json'
            path.write_bytes(revision.p.encoded({'name':'toddy-agent','installed':True}))
            with self.assertRaisesRegex(ValueError,'built-only'):revision.verified_built(path,Path(temporary))
            path.write_bytes(revision.p.encoded({'name':'foreign','installed':False}))
            with self.assertRaisesRegex(ValueError,'built-only'):revision.verified_built(path,Path(temporary))
    def test_installed_record_requires_real_full_flow_target_before_any_record_or_query(self):
        import native_acquisition_full_flow as flow
        with patch.object(flow,'guard',side_effect=ValueError('Actual installed disposable target absent')),patch.object(revision,'verified_built',side_effect=AssertionError('No package/readback on foreign target')):
            with self.assertRaisesRegex(ValueError,'Actual installed'):revision.installed_record(Path('/synthetic/built.json'),Path('/synthetic'),Path('/synthetic/result.json'))

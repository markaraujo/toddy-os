"""Input transfer cannot follow host links or include caches/unsafe source paths."""
import importlib.util
import io
from pathlib import Path
import sys
import tarfile
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts/host'))
spec=importlib.util.spec_from_file_location('sync_inputs',ROOT/'scripts/host/sync_build.py')
sync=importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync)


class InputTransfer(unittest.TestCase):
    def test_only_guarded_namespaces_and_regular_input_bytes_are_streamed(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            (root/'scripts/build/__pycache__').mkdir(parents=True)
            (root/'scripts/build/run_step.py').write_text('public recipe')
            (root/'scripts/build/__pycache__/ignored.pyc').write_bytes(b'cache')
            (root/'.local/sources').mkdir(parents=True)
            (root/'.local/sources/package.tar.xz').write_bytes(b'verified archive fixture')
            (root/'reference.log').write_text('public reference data')
            stream=io.BytesIO()
            sync.stream_inputs(stream,root,['scripts/build'],['package.tar.xz'],[('gcc',root/'reference.log')])
            stream.seek(0)
            with tarfile.open(fileobj=stream) as archive:
                names=archive.getnames()
                self.assertIn('opt/toddy-build/scripts/build/run_step.py',names)
                self.assertIn('mnt/lfs/sources/package.tar.xz',names)
                self.assertIn('mnt/lfs/sources/evidence/h07-gcc/reference.log',names)
                self.assertFalse(any('__pycache__' in n for n in names))
                self.assertTrue(all(n=='toddy-input-sync.complete.json' or n.startswith(('opt/toddy-build/','mnt/lfs/sources/')) for n in names))
                self.assertTrue(all(m.uid==0 and m.gid==0 for m in archive.getmembers()))

    def test_source_escape_and_host_symlinks_are_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            (root/'.local/sources').mkdir(parents=True)
            (root/'private.txt').write_text('not a build input')
            (root/'.local/sources/link.tar.xz').symlink_to(root/'private.txt')
            for name in ['../private.txt','/etc/passwd','bad\nname','link.tar.xz']:
                with self.assertRaises(ValueError):sync.safe_source(root,name)
            info=tarfile.TarInfo('opt/toddy-build/link')
            info.type=tarfile.SYMTYPE
            with self.assertRaises(ValueError):sync.metadata_filter(info)

    def test_incomplete_or_corrupt_bundle_is_rejected_before_commit(self):
        import hashlib,json
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            data=root/'opt/toddy-build/recipe.sh'
            data.parent.mkdir(parents=True)
            data.write_text('verified recipe')
            with self.assertRaises(ValueError):sync.verify_bundle(root)
            marker=root/'toddy-input-sync.complete.json'
            expected={'schema_version':1,'files':{'opt/toddy-build/recipe.sh':hashlib.sha256(data.read_bytes()).hexdigest()}}
            marker.write_text(json.dumps(expected))
            self.assertEqual(sync.verify_bundle(root),[data])
            data.write_text('changed after manifest creation')
            with self.assertRaises(ValueError):sync.verify_bundle(root)

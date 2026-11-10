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

class VerifiedReuse(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.base=Path(self.tmp.name);self.stage=self.base/'stage';self.root=self.base/'receiver'
        self.relative=Path('opt/toddy-build/scripts/build/test.sh');self.source=self.stage/self.relative;self.dest=self.root/self.relative
        self.source.parent.mkdir(parents=True);self.dest.parent.mkdir(parents=True)
        self.source.write_text('verified content');self.dest.write_text('verified content')
        self.source.chmod(0o755);self.dest.chmod(0o755)
    def test_unchanged_input_retains_inode_and_does_not_copy(self):
        import os
        from unittest.mock import patch
        before=self.dest.stat().st_ino;os.utime(self.dest,ns=(1,1))
        with patch.object(sync.shutil,'copy2',side_effect=AssertionError('Unchanged input copied')):
            self.assertEqual(sync.commit_verified_files(self.stage,[self.source],self.root),{'reused':1,'replaced':0})
        self.assertEqual(self.dest.stat().st_ino,before);self.assertEqual(self.dest.stat().st_mtime_ns,1)
    def test_changed_bytes_and_mode_are_replaced(self):
        self.dest.write_text('corrupt content')
        self.assertEqual(sync.commit_verified_files(self.stage,[self.source],self.root)['replaced'],1)
        self.assertEqual(self.dest.read_bytes(),self.source.read_bytes())
        self.dest.chmod(0o644)
        self.assertEqual(sync.commit_verified_files(self.stage,[self.source],self.root)['replaced'],1)
        self.assertEqual(self.dest.stat().st_mode&0o777,0o755)
    def test_partial_input_is_not_ignored_when_destination_matches(self):
        part=self.dest.with_name(self.dest.name+'.input-sync-part');part.write_text('uncertain prior write')
        with self.assertRaises(ValueError):sync.commit_verified_files(self.stage,[self.source],self.root)
        self.assertEqual(part.read_text(),'uncertain prior write')
    def test_destination_escape_is_refused(self):
        outside=self.base/'outside';outside.write_text('preserved')
        self.dest.unlink();self.dest.symlink_to(outside)
        with self.assertRaises(ValueError):sync.commit_verified_files(self.stage,[self.source],self.root)
        self.assertEqual(outside.read_text(),'preserved')

    def test_namespace_root_cannot_redirect_within_receiver(self):
        import shutil
        namespace=self.root/'opt/toddy-build'
        shutil.rmtree(namespace)
        elsewhere=self.root/'other';elsewhere.mkdir()
        namespace.symlink_to(elsewhere,target_is_directory=True)
        with self.assertRaises(ValueError):sync.commit_verified_files(self.stage,[self.source],self.root)
        self.assertEqual(list(elsewhere.iterdir()),[])
    def test_changed_xattr_is_not_reused(self):
        import os
        os.setxattr(self.dest,'user.toddy-test',b'old metadata')
        self.assertEqual(sync.commit_verified_files(self.stage,[self.source],self.root)['replaced'],1)
        self.assertEqual(os.listxattr(self.dest),os.listxattr(self.source))

"""Original payload staging is exact, private-state free and refuses output replay."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts/build/phase2'))
from executor_package import stage, MODULES


class ExecutorPackageTests(unittest.TestCase):
    def test_exact_source_owned_layout_and_no_authority_data(self):
        with tempfile.TemporaryDirectory() as name:
            destination=Path(name)/'stage';manifest=stage(destination,ROOT)
            for module in MODULES:
                output=destination/'usr/lib/toddy/executor'/module
                self.assertEqual(output.read_bytes(),(ROOT/'runtime/executor'/module).read_bytes())
                self.assertEqual(output.stat().st_mode&0o777,0o755 if module=='owner_policy.py' else 0o644)
            self.assertFalse((destination/'var').exists());self.assertFalse(manifest['bundled_grants'])
            self.assertEqual(manifest['runtime_state'],'/var/lib/toddy/executor')
            self.assertEqual((destination/'etc/systemd/system/multi-user.target.wants/toddy-executor.service').readlink(),Path('/usr/lib/systemd/system/toddy-executor.service'))
            activation=(destination/'usr/share/dbus-1/system-services/io.github.markaraujo.Toddy.Executor.service').read_text()
            self.assertIn('Exec=/usr/bin/false',activation);self.assertIn('SystemdService=toddy-executor.service',activation)
            self.assertEqual(json.loads((destination/'usr/share/doc/toddy-executor/source-manifest.json').read_text()),manifest)
            for relative,digest in manifest['inputs'].items():
                self.assertEqual(hashlib.sha256((ROOT/relative).read_bytes()).hexdigest(),digest)
            with self.assertRaisesRegex(ValueError,'new_canonical'):stage(destination,ROOT)

    def test_stage_is_deterministic(self):
        with tempfile.TemporaryDirectory() as name:
            a,b=Path(name)/'a',Path(name)/'b';stage(a,ROOT);stage(b,ROOT)
            files=lambda folder:{str(p.relative_to(folder)):str(p.readlink()) if p.is_symlink() else p.read_bytes() for p in folder.rglob('*') if p.is_file() or p.is_symlink()}
            self.assertEqual(files(a),files(b))
            for path in [*a.rglob('*'),a]:self.assertEqual(path.lstat().st_mtime,1794009600)


if __name__=='__main__':unittest.main()

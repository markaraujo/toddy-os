import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('package_backend',Path(__file__).resolve().parents[1]/'scripts/build/package_backend.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

class BackendTests(unittest.TestCase):
    def test_reject_unaccepted_native_marker(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'h07-dpkg.success.json').write_text(json.dumps({'recipe_exit':0,'postcheck_exit':1}))
            with self.assertRaises(SystemExit):module.PackageBackend(root,root)
    def test_bootstrap_has_explicit_root(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(module.subprocess,'run') as run:
            root=Path(tmp);backend=module.PackageBackend(root,root)
            backend.install(Path('/cache/probe.deb'))
            self.assertIn('--root='+str(root),run.call_args.args[0])
    def test_native_install_uses_chroot_owned_copy(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(module.subprocess,'run') as run:
            root=Path(tmp);(root/'sources').mkdir();archive=root/'probe.deb';archive.write_bytes(b'package')
            backend=module.PackageBackend(root,root);backend.native=True
            backend.install(archive)
            command=run.call_args.args[0]
            self.assertEqual(command[:3],['/usr/sbin/chroot',str(root),'/usr/bin/env'])
            self.assertEqual(command[-1],'/sources/native-package-output/probe.deb')
            self.assertFalse((root/'sources/native-package-output/probe.deb').exists())

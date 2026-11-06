import contextlib
import importlib.util
import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('kernel_config',Path(__file__).resolve().parents[1]/'scripts/build/h09/check_kernel_config.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)


class KernelConfigContract(unittest.TestCase):
    def run_check(self,fragment,resolved):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            (root/'Kconfig').write_text('config X86_NATIVE_CPU\n bool\nconfig VIRTIO_BLK\n tristate\n')
            (root/'requested').write_text(fragment)
            (root/'resolved').write_text(resolved)
            argv=['check',str(root/'requested'),str(root/'resolved'),'--source',str(root)]
            with patch.object(sys,'argv',argv),contextlib.redirect_stdout(io.StringIO()):module.main()

    def test_missing_required_root_driver_is_rejected(self):
        with self.assertRaises(SystemExit):
            self.run_check('CONFIG_VIRTIO_BLK=y\n','# CONFIG_VIRTIO_BLK is not set\n')

    def test_unknown_requested_symbol_is_rejected(self):
        with self.assertRaises(SystemExit):self.run_check('CONFIG_INVENTED=y\n','CONFIG_INVENTED=y\n')

    def test_machine_specific_cpu_is_rejected(self):
        with self.assertRaises(SystemExit):self.run_check('CONFIG_VIRTIO_BLK=y\n','CONFIG_VIRTIO_BLK=y\nCONFIG_X86_NATIVE_CPU=y\n')

    def test_hidden_disabled_symbol_may_be_omitted(self):
        self.run_check('# CONFIG_X86_NATIVE_CPU is not set\nCONFIG_VIRTIO_BLK=y\n','CONFIG_VIRTIO_BLK=y\n')

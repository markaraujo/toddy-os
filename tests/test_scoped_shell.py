"""Managed-shell guards must prevent dispatch when its lifecycle boundary is missing."""
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from runtime.tools.scoped import ScopedShell
from runtime.tools.native import ToolError


class ScopedShellTests(unittest.TestCase):
    def test_missing_parent_fails_before_process_dispatch(self):
        with tempfile.TemporaryDirectory() as root:
            with patch.object(ScopedShell,'_properties',return_value={}), patch('runtime.tools.scoped.subprocess.Popen') as spawn:
                with self.assertRaisesRegex(ToolError,'managed_shell_parent_unavailable'):
                    ScopedShell()(Path(root),['/usr/bin/true'])
                spawn.assert_not_called()

    def test_canceled_before_dispatch_needs_no_manager_or_process(self):
        with tempfile.TemporaryDirectory() as root:
            with patch.object(ScopedShell,'_properties') as manager, patch('runtime.tools.scoped.subprocess.Popen') as spawn:
                with self.assertRaisesRegex(ToolError,'canceled_before_dispatch'):
                    ScopedShell()(Path(root),['/usr/bin/true'],canceled=lambda:True)
                manager.assert_not_called();spawn.assert_not_called()

    def test_argument_and_parent_name_refusal(self):
        for name in ['--user','other.service','toddy-../x.service']:
            with self.assertRaises(ToolError):ScopedShell(name)
        with tempfile.TemporaryDirectory() as root:
            with patch.object(ScopedShell,'_properties') as manager:
                for argv in [['relative'],['/usr/bin/true','x\x00y'],[]]:
                    with self.assertRaisesRegex(ToolError,'invalid_shell_arguments'):ScopedShell()(Path(root),argv)
                manager.assert_not_called()


if __name__=='__main__':unittest.main()

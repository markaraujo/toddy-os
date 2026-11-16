"""Structured native control contracts; real Polkit/systemd qualification is separate."""
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'runtime/executor'))
from operations import validate
from store import PolicyError
from native_backends import service_operation, network_operation
import owner_policy


class NativeControlTests(unittest.TestCase):
    def test_no_argument_or_policy_injection(self):
        validate('service_operation', {'action': 'restart', 'unit': 'sshd.service'})
        for unit in ['--root=/tmp/foreign', '/etc/x.service', 'x\n.service', 'a.service;id', 'foo.socket', '../x.service']:
            with self.assertRaises(PolicyError):
                validate('service_operation', {'action': 'start', 'unit': unit})
        for args in [{'enabled': 1}, {'enabled': True, 'uid': 0}, {'enabled': 'yes'}]:
            with self.assertRaises(PolicyError):validate('network_operation', args)
        with self.assertRaises(PolicyError):validate('service_operation', {'action': 'enable', 'unit': 'x.service'})

    def test_postconditions_not_command_exit_decide_verification(self):
        with patch('native_backends.run_command', side_effect=[{'exit': 0}, {'exit': 0, '_private_output': b'inactive\n'}]):
            with self.assertRaisesRegex(PolicyError, 'service_postcondition_failed'):
                service_operation({'action': 'start', 'unit': 'x.service'}, lambda: False)
        with patch('native_backends.run_command', side_effect=[{'exit': 0}, {'exit': 0, '_private_output': b'disabled\n'}]):
            with self.assertRaisesRegex(PolicyError, 'network_postcondition_failed'):
                network_operation({'enabled': True}, lambda: False)
        with patch('native_backends.run_command', side_effect=[{'exit': 0}, {'exit': 0, '_private_output': b'active\n'}]) as run:
            self.assertTrue(service_operation({'action': 'restart', 'unit': 'x.service'}, lambda: False)['verified'])
            self.assertEqual(run.call_args_list[0].args[0]['argv'], ['/usr/bin/systemctl', 'restart', 'x.service'])

    def test_stop_prevents_any_native_dispatch(self):
        for function, args in [(service_operation, {'action': 'stop', 'unit': 'x.service'}),
                               (network_operation, {'enabled': False})]:
            with patch('native_backends.run_command') as run:
                with self.assertRaisesRegex(PolicyError, 'operation_canceled_before_dispatch'):
                    function(args, lambda: True)
                run.assert_not_called()

    def test_owner_identity_is_not_from_user_payload(self):
        with patch('owner_policy.os.getuid', return_value=1000), patch('owner_policy.os.geteuid', return_value=1000), patch.dict(os.environ, {'PKEXEC_UID': '1000'}):
            with self.assertRaisesRegex(PolicyError, 'owner_authentication_required'):owner_policy.caller_uid()
        with patch('owner_policy.os.getuid', return_value=0), patch('owner_policy.os.geteuid', return_value=0):
            for value in ['', '0', '-1', '1000x', '4294967295']:
                with patch.dict(os.environ, {'PKEXEC_UID': value}):
                    with self.assertRaises(PolicyError):owner_policy.caller_uid()
            with patch.dict(os.environ, {'PKEXEC_UID': '1000'}):self.assertEqual(owner_policy.caller_uid(), 1000)

    def test_session_comes_from_logind_and_must_match_owner(self):
        import subprocess
        with patch('owner_policy.subprocess.run', side_effect=[subprocess.CompletedProcess([], 0, 'c3\n'),
                    subprocess.CompletedProcess([], 0, 'Active=yes\nRemote=no\nUser=1000\n')]):
            self.assertEqual(owner_policy.active_session(1000), 'c3')
        for props in ['Active=no\nRemote=no\nUser=1000\n', 'Active=yes\nRemote=yes\nUser=1000\n', 'Active=yes\nRemote=no\nUser=1001\n']:
            with patch('owner_policy.subprocess.run', side_effect=[subprocess.CompletedProcess([], 0, 'c3\n'), subprocess.CompletedProcess([], 0, props)]):
                with self.assertRaisesRegex(PolicyError, 'active_owner_session_required'):owner_policy.active_session(1000)


if __name__ == '__main__':unittest.main()

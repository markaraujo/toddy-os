import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('python_qa_transfer', Path(__file__).resolve().parents[1] / 'scripts/build/python_qa_transfer.py')
policy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(policy)
OLD = '3.14.10-1+toddy1'
NEW = '3.14.10-1+toddy2'


class PythonQATransfer(unittest.TestCase):
    def action(self, core, qa=None, started=False):
        return policy.next_action(OLD, NEW, core, qa, transaction_started=started)

    def test_configured_predecessor_starts_with_core(self):
        self.assertEqual(self.action((OLD, policy.INSTALLED)), 'install_core')
        with self.assertRaises(ValueError):
            self.action((OLD, policy.INSTALLED), (NEW, policy.INSTALLED))

    def test_observed_old_version_half_install_requires_recorded_attempt(self):
        state = (OLD, 'install reinstreq half-installed')
        with self.assertRaises(ValueError):
            self.action(state)
        self.assertEqual(self.action(state, started=True), 'install_core')

    def test_partial_core_is_repaired_before_qa(self):
        self.assertEqual(self.action((NEW, 'install reinstreq half-installed'), started=True), 'install_core')
        for state in policy.CONFIGURABLE:
            with self.subTest(state=state):
                self.assertEqual(self.action((NEW, state), started=True), 'configure_core')
        with self.assertRaises(ValueError):
            self.action((NEW, 'install ok unpacked'))

    def test_qa_is_installed_or_configured_after_core(self):
        core = (NEW, policy.INSTALLED)
        self.assertEqual(self.action(core, started=True), 'install_qa')
        self.assertEqual(self.action(core, (NEW, 'install reinstreq half-installed'), True), 'install_qa')
        self.assertEqual(self.action(core, (NEW, 'install ok unpacked'), True), 'configure_qa')

    def test_completed_packages_require_verification_without_reinstall(self):
        state = (NEW, policy.INSTALLED)
        self.assertEqual(self.action(state, state), 'verify_complete')
        self.assertEqual(self.action(state, state, True), 'verify_complete')

    def test_json_state_pairs_are_supported_but_malformed_data_is_rejected(self):
        state = [NEW, policy.INSTALLED]
        self.assertEqual(self.action(state, state, True), 'verify_complete')
        for state in ('installed', [], [NEW], [NEW, None]):
            with self.subTest(state=state), self.assertRaises(ValueError):
                self.action(state, started=True)

    def test_unknown_state_or_transaction_identity_is_rejected(self):
        for core, qa in [(None, None), (('other-version', policy.INSTALLED), None),
                         ((NEW, policy.INSTALLED), (OLD, policy.INSTALLED)),
                         ((NEW, 'hold ok installed'), None)]:
            with self.subTest(core=core, qa=qa), self.assertRaises(ValueError):
                self.action(core, qa, True)
        with self.assertRaises(ValueError):
            policy.next_action(OLD, NEW, (OLD, policy.INSTALLED), None, transaction_started='false')


if __name__ == '__main__':
    unittest.main()

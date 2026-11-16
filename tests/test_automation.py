"""Canonical scheduler binding/quiet outbox host proofs, not native B08."""
import copy
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'runtime/broker'))
from automation import Automation, AutomationError, NativeHealth, ACTIONS
from profiles import ProfileStore
from scheduler import ScheduleError


class Health:
    services = ('fixture.service',)
    def __init__(self):
        self.condition = 'healthy'
        self.calls = []
        self.entered = None
        self.release = None
    def disk(self, budget):
        budget.check()
        self.calls.append('disk')
        if self.entered is not None:
            self.entered.set()
            if not self.release.wait(3):
                raise AssertionError('test did not release probe')
        budget.check()
        return {'condition': self.condition, 'actionable': self.condition != 'healthy',
                'details': {'free_bytes': 2000000000 - len(self.calls), 'total_bytes': 10000000000}}
    def service(self, unit, budget):
        budget.check()
        self.calls.append(unit)
        return {'condition': self.condition, 'actionable': self.condition != 'healthy',
                'details': {'unit': unit, 'active_state': 'active' if self.condition == 'healthy' else 'failed'}}


class AutomationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name)
        schema = json.loads((ROOT / 'config/phase2/profile.schema.json').read_text())
        self.config = json.loads((ROOT / 'config/phase2/profile/config.json').read_text())
        self.config['automation'] = {'enabled': True, 'workflow_ids': sorted(ACTIONS)}
        capabilities = {'tools': {'system-info'}, 'skills': {'explain-system'}, 'workflows': ACTIONS,
                        'extensions': set(), 'adapters': set()}
        self.profiles = ProfileStore(self.path / 'profile', 'toddy-default', schema, capabilities=capabilities)
        self.profiles.apply({'config.json': json.dumps(self.config).encode()}, expected_revision=None)
        self.now = 1000.
        self.owner = True
        self.standing = True
        self.health = Health()
        self.sent = []
        self.automation = self.new()

    def tearDown(self):
        self.temp.cleanup()

    def new(self, notifier=None):
        return Automation(self.profiles, owner_allowed=lambda: self.owner,
            standing_allowed=lambda action: self.standing, health=self.health,
            notifier=notifier or (lambda identifier, message: self.sent.append((identifier, message)) or True),
            clock=lambda: self.now)

    def configure(self, action='disk-health', **kwargs):
        values = {'interval': 60, 'next_due': self.now, 'max_runs': 30}
        values.update(kwargs)
        return self.automation.configure('health', action, **values)

    def enabled(self, action='disk-health', **kwargs):
        self.configure(action, **kwargs)
        self.automation.enable('health')

    def test_no_autostart_disabled_configuration_and_no_implicit_grant(self):
        self.assertEqual(self.health.calls, [])
        result = self.configure()
        self.assertFalse(result['enabled'])
        self.assertFalse(result['standing_grant_created'])
        self.assertEqual(self.automation.poll()['runs'], [])
        self.standing = False
        with self.assertRaisesRegex(ScheduleError, 'authorization'):
            self.automation.enable('health')
        self.assertEqual(self.health.calls, [])

    def test_actual_read_only_disk_probe_and_fixed_service_argv(self):
        class Budget:
            deadline = 1000
            class scheduler:
                monotonic = staticmethod(lambda: 999)
            def check(self):
                pass
        native = NativeHealth(self.path, services=('fixture.service',))
        disk = native.disk(Budget())
        self.assertGreater(disk['details']['total_bytes'], 0)
        class Result:
            returncode = 0
            stdout = b'active\n'
        with patch('automation.subprocess.run', return_value=Result()) as run:
            self.assertFalse(native.service('fixture.service', Budget())['actionable'])
            self.assertEqual(run.call_args.args[0], ['/usr/bin/systemctl', 'show', '--property=ActiveState', '--value', '--', 'fixture.service'])
            self.assertLessEqual(run.call_args.kwargs['timeout'], 2)
        with self.assertRaisesRegex(AutomationError, 'service_scope'):
            native.service('other.service', Budget())

    def test_once_restart_and_unchanged_health_stays_quiet_without_model_calls(self):
        self.enabled()
        self.assertEqual(self.automation.poll()['runs'][0]['state'], 'completed')
        self.assertEqual(self.automation.poll()['runs'], [])
        self.automation = self.new()
        self.assertEqual(self.automation.recover()['uncertain_runs'], 0)
        self.now += 60
        self.automation.poll()
        self.assertEqual(self.health.calls, ['disk', 'disk'])
        self.assertEqual(self.sent, [])
        self.assertEqual(len(self.automation.inspect()['runs']), 2)

    def test_one_actionable_change_notifies_once_then_remains_quiet(self):
        self.enabled()
        self.health.condition = 'low-space'
        first = self.automation.poll()
        self.assertEqual(first['notifications_sent'], 1)
        self.now += 60
        self.automation = self.new()
        second = self.automation.poll()
        self.assertEqual(second['notifications_sent'], 0)
        self.assertEqual(len(self.sent), 1)
        self.assertEqual(self.sent[0][1]['condition'], 'low-space')
        self.assertEqual(self.automation.inspect()['notifications'][0]['state'], 'sent')

    def test_service_health_records_only_registered_units_and_actual_conditions(self):
        self.enabled('service-health')
        self.health.condition = 'service-unavailable'
        result = self.automation.poll()
        self.assertEqual(result['runs'][0]['state'], 'completed')
        self.assertEqual(self.health.calls, ['fixture.service'])
        self.assertEqual(self.sent[0][1]['details']['unit'], 'fixture.service')

    def test_revocation_between_enable_and_dispatch_prevents_probe_and_notice(self):
        self.enabled()
        self.standing = False
        self.assertEqual(self.automation.poll()['runs'][0]['state'], 'denied')
        self.assertEqual(self.health.calls, [])
        self.assertEqual(self.sent, [])
        self.assertEqual(self.automation.poll()['runs'], [])

    def test_profile_reset_disables_work_even_if_old_scheduler_flag_remains_enabled(self):
        self.enabled()
        config = copy.deepcopy(self.config)
        config['automation'] = {'enabled': False, 'workflow_ids': []}
        self.profiles.apply({'config.json': json.dumps(config).encode()}, expected_revision=self.profiles.current())
        self.assertEqual(self.automation.poll()['runs'][0]['state'], 'denied')
        self.assertEqual(self.health.calls, [])

    def test_private_lease_prevents_overlapping_poll_instances(self):
        self.enabled()
        self.health.entered, self.health.release = threading.Event(), threading.Event()
        first = self.automation
        second = self.new()
        results = []
        worker = threading.Thread(target=lambda: results.append(first.poll()))
        worker.start()
        try:
            self.assertTrue(self.health.entered.wait(3))
            self.assertEqual(second.poll()['state'], 'lease-busy')
        finally:
            self.health.release.set()
            worker.join(3)
        self.assertFalse(worker.is_alive())
        self.assertEqual(len(self.health.calls), 1)
        self.assertEqual(results[0]['runs'][0]['state'], 'completed')

    def test_stop_reports_active_read_and_never_replays_uncertain_run(self):
        self.enabled()
        self.health.entered, self.health.release = threading.Event(), threading.Event()
        results = []
        worker = threading.Thread(target=lambda: results.append(self.automation.poll()))
        worker.start()
        try:
            self.assertTrue(self.health.entered.wait(3))
            self.assertTrue(self.automation.stop()['active_read_may_finish'])
        finally:
            self.health.release.set()
            worker.join(3)
        self.assertFalse(worker.is_alive())
        self.assertEqual(results[0]['runs'][0]['state'], 'requires-review')
        self.assertEqual(self.automation.inspect()['runs'][0]['state'], 'uncertain')
        restarted = self.new()
        restarted.recover()
        self.now += 60
        restarted.poll()
        self.assertEqual(len(self.health.calls), 1)
        operation = restarted.inspect()['runs'][0]['operation_id']
        self.assertFalse(restarted.acknowledge_read_only_failure(operation)['replayed'])
        self.assertEqual(restarted.inspect()['runs'][0]['state'], 'failed')

    def test_lost_notification_ack_is_uncertain_and_is_never_automatically_sent_twice(self):
        calls = []
        def lost(identifier, message):
            calls.append(identifier)
            raise AutomationError('acknowledgement_lost_fixture')
        self.automation = self.new(notifier=lost)
        self.enabled()
        self.health.condition = 'low-space'
        self.automation.poll()
        self.assertEqual(self.automation.inspect()['notifications'][0]['state'], 'uncertain')
        restarted = self.new(notifier=lost)
        restarted.recover()
        self.now += 60
        restarted.poll()
        self.assertEqual(len(calls), 1)

    def test_cancel_denies_pending_notice_before_transport_is_attached(self):
        self.enabled()
        self.automation.notifier = None
        self.health.condition = 'low-space'
        self.automation.poll()
        self.assertEqual(self.automation.inspect()['notifications'][0]['state'], 'pending')
        self.automation.cancel('health')
        self.automation = self.new()
        self.automation.poll()
        self.assertEqual(self.sent, [])
        self.assertEqual(self.automation.inspect()['notifications'][0]['state'], 'denied')

    def test_outbox_full_rolls_back_fingerprint_and_latest_observation(self):
        self.enabled()
        with self.profiles._db() as db:
            db.executemany('INSERT INTO automation_notifications VALUES(?,?,?,?,?,?,?,?)',
                [('old-' + str(index), 'toddy-default', 'health', 'old-operation-' + str(index), 'disk-health', '{}', 'sent', 1) for index in range(256)])
        self.health.condition = 'low-space'
        result = self.automation.poll()
        self.assertEqual(result['runs'][0]['code'], 'automation_notification_storage_full')
        self.assertEqual(self.automation.inspect()['observations'], [])
        with self.profiles._db() as db:
            self.assertEqual(db.execute('SELECT count(*) FROM scheduler_health').fetchone()[0], 0)

    def test_missed_skip_budget_and_owner_controls_do_not_create_authority(self):
        self.enabled(max_runs=1)
        self.now += 181
        self.assertEqual(self.automation.poll()['runs'][0]['state'], 'skipped')
        self.assertEqual(self.health.calls, [])
        self.assertEqual(self.automation.poll()['runs'], [])
        with self.assertRaisesRegex(AutomationError, 'time_budget'):
            self.configure(seconds=11)
        self.owner = False
        with self.assertRaisesRegex(AutomationError, 'authenticated_owner'):
            self.automation.cancel('health')

    def test_retention_cleanup_preserves_unknown_runs_and_notification_sends(self):
        self.configure()
        with self.profiles._db() as db:
            db.executemany('INSERT INTO scheduler_runs(operation_id,profile_id,job_id,due,state) VALUES(?,?,?,?,?)',
                [('old-complete', 'toddy-default', 'health', 1, 'completed'),
                 ('old-unknown', 'toddy-default', 'health', 2, 'uncertain')])
            db.executemany('INSERT INTO automation_notifications VALUES(?,?,?,?,?,?,?,?)',
                [('old-sent', 'toddy-default', 'health', 'old-complete', 'disk-health', '{}', 'sent', 1),
                 ('old-unknown', 'toddy-default', 'health', 'old-unknown', 'disk-health', '{}', 'uncertain', 2)])
        self.now += 40 * 86400
        result = self.automation.prune_terminal_history()
        self.assertEqual(result['terminal_runs_removed'], 1)
        self.assertEqual(result['terminal_notifications_removed'], 1)
        state = self.automation.inspect()
        self.assertEqual(state['runs'][0]['state'], 'uncertain')
        self.assertEqual(state['notifications'][0]['state'], 'uncertain')


if __name__ == '__main__':
    unittest.main()

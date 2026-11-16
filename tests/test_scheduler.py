"""Focused deterministic scheduler host checks; no native B08 acceptance."""
import multiprocessing
from pathlib import Path
import sqlite3
import sys
import tempfile
import time
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'runtime/broker'))
from scheduler import Scheduler, ScheduleError


def crash_worker(path, marker):
    db = sqlite3.connect(path, isolation_level=None)
    scheduler = Scheduler(db, 'primary', clock=lambda: 1000)
    def effect(operation, budget):
        Path(marker).write_text(operation)
        time.sleep(30)
        return {'verified': True}
    scheduler.run_due('health', authorize=lambda _: True, actions={'disk-check': effect})


class SchedulerTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:', isolation_level=None)
        self.now = 1000
        self.mono = 10
        self.scheduler = Scheduler(self.db, 'primary', clock=lambda: self.now, monotonic=lambda: self.mono)
        self.calls = []

    def tearDown(self):
        self.db.close()

    def configure(self, key='health', **kwargs):
        self.scheduler.configure(key, 'disk-check', interval=60, next_due=self.now, **kwargs)

    def action(self, operation, budget):
        budget.check()
        self.calls.append(operation)
        return {'verified': True}

    def run_due(self, **kwargs):
        return self.scheduler.run_due('health', authorize=kwargs.get('authorize', lambda _: True), actions={'disk-check': kwargs.get('action', self.action)})

    def enable(self, key='health'):
        self.scheduler.enable(key, authorize=lambda _: True)

    def test_disabled_by_default_current_authorization_and_one_run_budget(self):
        self.configure(max_runs=1)
        self.assertEqual(self.run_due()['state'], 'idle')
        with self.assertRaisesRegex(ScheduleError, 'authorization'):
            self.scheduler.enable('health', authorize=lambda _: False)
        self.enable()
        self.assertEqual(self.run_due()['state'], 'completed')
        self.now += 60
        self.assertEqual(self.run_due()['state'], 'idle')
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(self.scheduler.history()[0]['state'], 'completed')

    def test_restart_keeps_next_slot_and_never_replays_completed_work(self):
        self.configure()
        self.enable()
        self.run_due()
        self.scheduler = Scheduler(self.db, 'primary', clock=lambda: self.now)
        self.assertEqual(self.scheduler.recover(), 0)
        self.assertEqual(self.run_due()['state'], 'idle')
        self.assertEqual(len(self.calls), 1)

    def test_missed_skip_records_once_and_run_once_catchup_is_bounded(self):
        self.configure()
        self.enable()
        self.now += 181
        self.assertEqual(self.run_due()['state'], 'skipped')
        self.assertEqual(self.run_due()['state'], 'idle')
        self.assertEqual(self.calls, [])
        self.scheduler.configure('catchup', 'disk-check', interval=60, next_due=1000, missed='run-once', catchup=300)
        self.enable('catchup')
        result = self.scheduler.run_due('catchup', authorize=lambda _: True, actions={'disk-check': self.action})
        self.assertEqual(result['state'], 'completed')
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(self.scheduler.run_due('catchup', authorize=lambda _: True, actions={'disk-check': self.action})['state'], 'idle')

    def test_claim_is_durable_no_overlap_and_revocation_before_effect(self):
        self.configure()
        self.configure('second')
        self.enable()
        self.enable('second')
        def effect(operation, budget):
            self.assertFalse(self.db.in_transaction)
            self.assertEqual(self.scheduler.run_due('second', authorize=lambda _: True, actions={'disk-check': self.action})['state'], 'busy')
            return {'verified': True}
        self.assertEqual(self.run_due(action=effect)['state'], 'completed')
        self.assertEqual(self.scheduler.run_due('second', authorize=lambda _: False, actions={'disk-check': self.action})['state'], 'denied')
        self.assertEqual(self.calls, [])

    def test_stop_disables_new_work_and_reports_inflight_completion(self):
        self.configure()
        self.enable()
        def effect(operation, budget):
            self.assertFalse(budget.canceled())
            ack = self.scheduler.cancel('health')
            self.assertTrue(ack['active_write_may_finish'])
            self.assertTrue(budget.canceled())
            return {'verified': True}  # real backend reached safe commit
        self.assertEqual(self.run_due(action=effect)['state'], 'completed')
        self.assertEqual(self.scheduler.history()[0]['cancel_requested'], 1)
        self.now += 60
        self.assertEqual(self.run_due()['state'], 'idle')

    def test_callback_failure_or_deadline_becomes_uncertain_no_retry(self):
        self.configure(seconds=1)
        self.enable()
        def effect(operation, budget):
            self.calls.append(operation)
            self.mono += 2
            budget.check()
        with self.assertRaises(ScheduleError):
            self.run_due(action=effect)
        self.assertEqual(self.scheduler.history()[0]['state'], 'uncertain')
        self.now += 60
        self.assertEqual(self.run_due()['state'], 'idle')
        with self.assertRaisesRegex(ScheduleError, 'uncertain'):
            self.enable()
        self.assertEqual(len(self.calls), 1)

    def test_health_is_quiet_for_unchanged_actionable_condition(self):
        self.db.row_factory = sqlite3.Row
        self.assertFalse(self.scheduler.observe('disk', state='healthy', actionable=False)['notify'])
        self.assertFalse(self.scheduler.observe('disk', state='healthy', actionable=False)['notify'])
        self.assertTrue(self.scheduler.observe('disk', state='low-space', actionable=True)['notify'])
        self.scheduler = Scheduler(self.db, 'primary')
        self.assertFalse(self.scheduler.observe('disk', state='low-space', actionable=True)['notify'])
        self.assertFalse(self.scheduler.observe('disk', state='healthy', actionable=False)['notify'])
        self.assertTrue(self.scheduler.observe('disk', state='low-space', actionable=True)['notify'])

    def test_import_profile_clone_is_disabled_and_does_not_copy_history(self):
        self.configure()
        self.enable()
        self.run_due()
        exported = self.scheduler.export()
        other = Scheduler(self.db, 'secondary', clock=lambda: self.now)
        other.import_disabled(exported)
        self.assertEqual(other.history(), [])
        self.now += 60
        self.assertEqual(other.run_due('health', authorize=lambda _: True, actions={'disk-check': self.action})['state'], 'idle')
        self.assertNotIn('enabled', exported['jobs'][0])
        malicious = {'scheduler_version': 1, 'timezone': 'UTC', 'jobs': [dict(exported['jobs'][0], enabled=1)]}
        third = Scheduler(self.db, 'third')
        with self.assertRaisesRegex(ScheduleError, 'import_fields'):
            third.import_disabled(malicious)
        self.assertEqual(third.export()['jobs'], [])

    def test_outer_transaction_never_dispatches_undurable_effect(self):
        self.configure()
        self.enable()
        self.db.execute('BEGIN')
        with self.assertRaisesRegex(ScheduleError, 'outer_transaction'):
            self.run_due()
        self.db.rollback()
        self.assertEqual(self.calls, [])

    def test_killed_effect_is_retained_uncertain_and_never_replayed(self):
        with tempfile.TemporaryDirectory() as temp:
            path = str(Path(temp) / 'state.sqlite')
            marker = str(Path(temp) / 'effect')
            db = sqlite3.connect(path, isolation_level=None)
            try:
                db.execute('PRAGMA journal_mode=WAL')
                scheduler = Scheduler(db, 'primary', clock=lambda: 1000)
                scheduler.configure('health', 'disk-check', interval=60, next_due=1000)
                scheduler.enable('health', authorize=lambda _: True)
                process = multiprocessing.Process(target=crash_worker, args=(path, marker))
                process.start()
                try:
                    deadline = time.monotonic() + 5
                    while not Path(marker).exists() and time.monotonic() < deadline:
                        time.sleep(.01)
                    self.assertTrue(Path(marker).exists())
                    process.terminate()
                    process.join(5)
                    self.assertFalse(process.is_alive())
                finally:
                    if process.is_alive():
                        process.kill()
                        process.join()
                operation = Path(marker).read_text()
                self.assertEqual(scheduler.recover(), 1)
                self.assertEqual(scheduler.history()[0]['operation_id'], operation)
                self.assertEqual(scheduler.history()[0]['state'], 'uncertain')
                self.assertEqual(scheduler.run_due('health', authorize=lambda _: True, actions={'disk-check': lambda *_: self.fail('replayed')})['state'], 'idle')
                self.assertEqual(db.execute('PRAGMA integrity_check').fetchone()[0], 'ok')
            finally:
                db.close()


if __name__ == '__main__':
    unittest.main()

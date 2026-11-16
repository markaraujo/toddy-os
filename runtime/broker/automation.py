"""Quiet deterministic health workflow binding for the canonical broker store.

No model/provider, implicit background startup, imported executable workflow,
credential or grant. The service supplies current authenticated owner/standing
policy predicates; configuration alone cannot authorize a scheduled operation.
"""
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import threading
import time

try:
    from .scheduler import Scheduler, ScheduleError
    from .protocol import strict_json
except ImportError:
    from scheduler import Scheduler, ScheduleError
    from protocol import strict_json

ACTIONS = {'disk-health', 'service-health'}
UNIT = re.compile(r'[A-Za-z0-9@_.:-]{1,128}\.service\Z')


class AutomationError(ValueError):
    pass


class NativeHealth:
    """Read the local root filesystem and a fixed selected system-service list.

    Condition labels, rather than varying byte counts, drive quiet notifications.
    No service is started/restarted and no privileged mutation is performed.
    """
    def __init__(self, disk_path='/', *, services=('NetworkManager.service', 'gdm.service')):
        self.disk_path = Path(disk_path)
        if not self.disk_path.is_absolute() or self.disk_path.resolve() != self.disk_path or not self.disk_path.is_dir():
            raise AutomationError('automation_disk_scope')
        if not isinstance(services, tuple) or not 1 <= len(services) <= 4 or any(not isinstance(unit, str) or not UNIT.fullmatch(unit) for unit in services):
            raise AutomationError('automation_service_scope')
        self.services = services

    def disk(self, budget):
        budget.check()
        sample = os.statvfs(self.disk_path)
        free, total = sample.f_bavail * sample.f_frsize, sample.f_blocks * sample.f_frsize
        if not 0 <= free <= total <= 2**53 - 1:
            raise AutomationError('automation_disk_sample')
        condition = ('critical-space' if free < 512 * 1024**2 else
                     'low-space' if free < max(1024**3, total // 10) else 'healthy')
        budget.check()
        return {'condition': condition, 'actionable': condition != 'healthy',
                'details': {'free_bytes': free, 'total_bytes': total}}

    def service(self, unit, budget):
        if unit not in self.services:
            raise AutomationError('automation_service_scope')
        budget.check()
        remaining = budget.deadline - budget.scheduler.monotonic()
        if remaining <= 0:
            raise ScheduleError('schedule_canceled_or_deadline')
        try:
            result = subprocess.run(['/usr/bin/systemctl', 'show', '--property=ActiveState', '--value', '--', unit],
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL,
                env={'PATH': '/usr/bin:/bin', 'LC_ALL': 'C'}, timeout=min(2, remaining), check=False)
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise AutomationError('automation_service_probe_unavailable') from exc
        state = result.stdout.decode('utf-8', errors='strict').strip()
        if result.returncode or state not in {'active', 'inactive', 'failed', 'activating', 'deactivating', 'reloading', 'maintenance', 'refreshing'}:
            raise AutomationError('automation_service_sample')
        budget.check()
        condition = 'healthy' if state in ('active', 'activating', 'reloading', 'refreshing') else 'service-unavailable'
        return {'condition': condition, 'actionable': condition != 'healthy', 'details': {'unit': unit, 'active_state': state}}


class DesktopNotifier:
    """Actual session notification roundtrip, bounded independently of a model.

    Optional native GI/D-Bus availability is checked only when a reviewed pending
    event is delivered. Never fall back to email, an external command or provider.
    """
    def __call__(self, notification_id, message):
        try:
            from gi.repository import Gio, GLib
            connection = Gio.bus_get_sync(Gio.BusType.SESSION, None)
            portuguese = message.get('locale', 'en').startswith('pt')
            body = (('O espaço em disco precisa de atenção.' if portuguese else 'Disk space needs attention.')
                    if message['action'] == 'disk-health' else
                    ('Um serviço selecionado não está em execução: ' if portuguese else 'A selected service is not running: ') + message['details']['unit'])
            reply = connection.call_sync('org.freedesktop.Notifications', '/org/freedesktop/Notifications',
                'org.freedesktop.Notifications', 'Notify',
                GLib.Variant('(susssasa{sv}i)', ('Toddy', 0, 'io.github.markaraujo.Toddy',
                    'Toddy system health', body, [], {}, 10000)), GLib.VariantType('(u)'),
                Gio.DBusCallFlags.NONE, 2000, None)
            if reply.unpack()[0] <= 0:
                raise AutomationError('automation_notification_unverified')
        except Exception as exc:
            raise AutomationError('automation_notification_unavailable') from exc
        return True


class Automation:
    def __init__(self, profiles, *, owner_allowed=lambda: False, standing_allowed=lambda action: False,
                 health=None, notifier=None, clock=time.time, monotonic=time.monotonic):
        self.profiles = profiles
        self.owner_allowed = owner_allowed
        self.standing_allowed = standing_allowed
        self.health = health if health is not None else NativeHealth()
        self.notifier = notifier
        self.clock, self.monotonic = clock, monotonic
        self._stopping = threading.Event()
        with self._scheduler() as scheduler:
            with scheduler._transaction():
                scheduler.db.execute('''CREATE TABLE IF NOT EXISTS automation_observations(
                    profile_id TEXT NOT NULL,probe_id TEXT NOT NULL,operation_id TEXT NOT NULL,
                    condition TEXT NOT NULL,details TEXT NOT NULL,observed REAL NOT NULL,
                    PRIMARY KEY(profile_id,probe_id))''')
                scheduler.db.execute('''CREATE TABLE IF NOT EXISTS automation_notifications(
                    id TEXT PRIMARY KEY,profile_id TEXT NOT NULL,job_id TEXT NOT NULL,
                    operation_id TEXT NOT NULL,action TEXT NOT NULL,
                    body TEXT NOT NULL,state TEXT NOT NULL,created REAL NOT NULL)''')

    @contextmanager
    def _scheduler(self):
        with self.profiles._db() as db:
            yield Scheduler(db, self.profiles.profile_id, clock=self.clock, monotonic=self.monotonic)

    @contextmanager
    def _lease(self):
        path = self.profiles.directory / '.automation.lock'
        fd = os.open(path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600)
        try:
            info = os.fstat(fd)
            if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != 0o600 or info.st_nlink != 1:
                raise AutomationError('automation_private_lease')
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise AutomationError('automation_lease_busy') from exc
            yield
        finally:
            os.close(fd)

    def _owner(self):
        if self.owner_allowed() is not True:
            raise AutomationError('automation_authenticated_owner_required')

    def _allowed(self, action):
        if not isinstance(action, str) or action not in ACTIONS or self._stopping.is_set():
            return False
        config = strict_json(self.profiles.snapshot()['config.json'])
        return (config['automation']['enabled'] is True and action in config['automation']['workflow_ids']
                and self.standing_allowed(action) is True)

    def configure(self, job_id, action, **settings):
        self._owner()
        if not isinstance(action, str) or action not in ACTIONS:
            raise AutomationError('automation_unregistered_workflow')
        if type(settings.get('seconds', 10)) is not int or not 1 <= settings.get('seconds', 10) <= 10:
            raise AutomationError('automation_workflow_time_budget')
        with self._lease(), self._scheduler() as scheduler:
            due = settings.get('next_due')
            if scheduler.db.execute('SELECT 1 FROM scheduler_runs WHERE profile_id=? AND job_id=? AND due=?',
                    (self.profiles.profile_id, job_id, due)).fetchone():
                raise AutomationError('automation_existing_slot_not_replayable')
            scheduler.configure(job_id, action, **settings)
            with scheduler._transaction():
                scheduler.db.execute("UPDATE automation_notifications SET state='denied' WHERE profile_id=? AND job_id=? AND state='pending'", (self.profiles.profile_id, job_id))
        return {'configured': True, 'enabled': False, 'standing_grant_created': False}

    def enable(self, job_id):
        self._owner()
        with self._lease(), self._scheduler() as scheduler:
            stopped = self._stopping.is_set()
            self._stopping.clear()  # New explicit owner action only.
            try:
                scheduler.enable(job_id, authorize=self._allowed)
            except BaseException:
                if stopped:
                    self._stopping.set()
                raise
        return {'enabled': True, 'standing_grant_created': False}

    def cancel(self, job_id):
        self._owner()
        with self._scheduler() as scheduler:
            with scheduler._transaction():
                result = scheduler.cancel_in_transaction(job_id)
                scheduler.db.execute("UPDATE automation_notifications SET state='denied' WHERE profile_id=? AND job_id=? AND state='pending'", (self.profiles.profile_id, job_id))
                return result

    def _probe(self, scheduler, operation_id, action, budget):
        operation = scheduler.db.execute('SELECT job_id FROM scheduler_runs WHERE operation_id=? AND profile_id=?', (operation_id, self.profiles.profile_id)).fetchone()
        if operation is None:
            raise AutomationError('automation_operation_binding_unavailable')
        samples = [('disk', lambda: self.health.disk(budget))] if action == 'disk-health' else [
            ('service-' + hashlib.sha256(unit.encode()).hexdigest()[:16],
             lambda unit=unit: self.health.service(unit, budget)) for unit in self.health.services]
        for probe_id, observe in samples:
            if self._stopping.is_set() or not self._allowed(action):
                raise AutomationError('automation_current_authorization_revoked')
            budget.check()
            sample = observe()
            if not isinstance(sample, dict) or set(sample) != {'condition', 'actionable', 'details'} or not isinstance(sample['details'], dict):
                raise AutomationError('automation_observation_schema')
            locale = strict_json(self.profiles.snapshot()['config.json'])['locale']
            body = json.dumps({'action': action, 'probe_id': probe_id, 'locale': locale, **sample}, sort_keys=True, allow_nan=False)
            if len(body.encode()) > 4096:
                raise AutomationError('automation_observation_limit')
            strict_json(body.encode())
            budget.check()
            if self._stopping.is_set() or not self._allowed(action):
                raise AutomationError('automation_current_authorization_revoked')
            with scheduler._transaction():
                budget.check()  # cancel cannot race the atomic observation/outbox
                quiet = scheduler.observe_in_transaction(probe_id, state=sample['condition'], actionable=sample['actionable'])
                scheduler.db.execute('INSERT OR REPLACE INTO automation_observations VALUES(?,?,?,?,?,?)',
                    (self.profiles.profile_id, probe_id, operation_id, sample['condition'],
                     json.dumps(sample['details'], sort_keys=True), self.clock()))
                if quiet['notify']:
                    if scheduler.db.execute('SELECT count(*) FROM automation_notifications WHERE profile_id=?', (self.profiles.profile_id,)).fetchone()[0] >= 256:
                        raise AutomationError('automation_notification_storage_full')
                    scheduler.db.execute('INSERT INTO automation_notifications VALUES(?,?,?,?,?,?,?,?)',
                        ('notice-' + operation_id + '-' + probe_id, self.profiles.profile_id,
                         operation['job_id'], operation_id, action, body, 'pending', self.clock()))
        return {'verified': True}

    def _deliver(self, scheduler):
        if self.notifier is None:
            return 0
        delivered = 0
        rows = scheduler.db.execute("SELECT id,action,body FROM automation_notifications WHERE profile_id=? AND state='pending' ORDER BY created,id LIMIT 4", (self.profiles.profile_id,)).fetchall()
        for row in rows:
            if not self._allowed(row['action']):
                with scheduler._transaction():
                    scheduler.db.execute("UPDATE automation_notifications SET state='denied' WHERE id=? AND state='pending'", (row['id'],))
                continue
            with scheduler._transaction():
                changed = scheduler.db.execute("UPDATE automation_notifications SET state='sending' WHERE id=? AND state='pending'", (row['id'],)).rowcount
            if not changed:
                continue
            if not self._allowed(row['action']):
                with scheduler._transaction():
                    scheduler.db.execute("UPDATE automation_notifications SET state='denied' WHERE id=?", (row['id'],))
                continue
            # Never retry a send whose acknowledgement was lost. No DB lock is
            # held during the real desktop transport callback.
            try:
                if self.notifier(row['id'], strict_json(row['body'].encode())) is not True:
                    raise AutomationError('automation_notification_unverified')
            except Exception:
                state = 'uncertain'
            else:
                state = 'sent'
                delivered += 1
            with scheduler._transaction():
                scheduler.db.execute('UPDATE automation_notifications SET state=? WHERE id=?', (state, row['id']))
        return delivered

    def poll(self):
        """One explicit bounded scheduler tick; never starts a second writer."""
        if self._stopping.is_set():
            return {'state': 'stopped', 'runs': [], 'notifications_sent': 0}
        try:
            with self._lease(), self._scheduler() as scheduler:
                deadline = self.monotonic() + 10
                jobs = scheduler.db.execute('SELECT id FROM scheduler_jobs WHERE profile_id=? AND enabled=1 AND next_due<=? ORDER BY next_due,id LIMIT 2', (self.profiles.profile_id, self.clock())).fetchall()
                runs = []
                actions = {action: (lambda op, budget, action=action: self._probe(scheduler, op, action, budget)) for action in ACTIONS}
                for job in jobs:
                    if self._stopping.is_set() or self.monotonic() >= deadline:
                        break
                    try:
                        runs.append(scheduler.run_due(job['id'], authorize=self._allowed, actions=actions))
                    except (ScheduleError, AutomationError, OSError, ValueError) as exc:
                        code = str(exc) if isinstance(exc, (ScheduleError, AutomationError)) and re.fullmatch('[a-z][a-z0-9_]{0,127}', str(exc)) else 'automation_probe_unavailable'
                        runs.append({'state': 'requires-review', 'job_id': job['id'], 'code': code})
                return {'state': 'polled', 'runs': runs, 'notifications_sent': self._deliver(scheduler)}
        except AutomationError as exc:
            if str(exc) == 'automation_lease_busy':
                return {'state': 'lease-busy', 'runs': [], 'notifications_sent': 0}
            raise

    def recover(self):
        """Explicit startup reconciliation only after the previous writer is gone."""
        with self._lease(), self._scheduler() as scheduler:
            interrupted = scheduler.recover()
            with scheduler._transaction():
                sends = scheduler.db.execute("UPDATE automation_notifications SET state='uncertain' WHERE profile_id=? AND state='sending'", (self.profiles.profile_id,)).rowcount
            return {'uncertain_runs': interrupted, 'uncertain_notifications': sends, 'automatic_replay': False}

    def inspect(self, *, limit=64):
        self._owner()
        if type(limit) is not int or not 1 <= limit <= 128:
            raise AutomationError('automation_history_limit')
        with self._scheduler() as scheduler:
            observations = [dict(row) for row in scheduler.db.execute('SELECT probe_id,operation_id,condition,details,observed FROM automation_observations WHERE profile_id=? ORDER BY probe_id', (self.profiles.profile_id,))]
            notifications = [dict(row) for row in scheduler.db.execute('SELECT id,action,state,created FROM automation_notifications WHERE profile_id=? ORDER BY created DESC,id DESC LIMIT ?', (self.profiles.profile_id, limit))]
            jobs = [dict(row) for row in scheduler.db.execute('SELECT id,action,interval,next_due,missed,catchup,seconds,remaining,enabled FROM scheduler_jobs WHERE profile_id=? ORDER BY id', (self.profiles.profile_id,))]
            return {'jobs': jobs, 'stopped': self._stopping.is_set(), 'runs': [dict(row) for row in reversed(scheduler.db.execute('SELECT operation_id,job_id,due,state,cancel_requested,result FROM scheduler_runs WHERE profile_id=? ORDER BY due DESC,operation_id DESC LIMIT ?', (self.profiles.profile_id, limit)).fetchall())], 'observations': observations, 'notifications': notifications,
                    'run_count': scheduler.db.execute('SELECT count(*) FROM scheduler_runs WHERE profile_id=?', (self.profiles.profile_id,)).fetchone()[0],
                    'desktop_transport_configured': self.notifier is not None}

    def prune_terminal_history(self):
        """Explicit owner cleanup after the documented 30 day terminal retention.

        Unknown sends/runs are never removed to regain dispatch capacity.
        """
        self._owner()
        cutoff = self.clock() - 30 * 86400
        with self._lease(), self._scheduler() as scheduler:
            with scheduler._transaction():
                notices = scheduler.db.execute("DELETE FROM automation_notifications WHERE profile_id=? AND created<? AND state IN ('sent','denied')", (self.profiles.profile_id, cutoff)).rowcount
                runs = scheduler.db.execute("DELETE FROM scheduler_runs WHERE profile_id=? AND due<? AND state IN ('completed','failed','skipped','denied')", (self.profiles.profile_id, cutoff)).rowcount
        return {'terminal_runs_removed': runs, 'terminal_notifications_removed': notices,
                'uncertain_state_preserved': True}

    def acknowledge_read_only_failure(self, operation_id):
        """Explicit owner review; retire a held read-only run without replay.

        No arbitrary/admin workflow may use this path. Unknown notification
        sends remain uncertain, and new execution needs a new slot/enable action.
        """
        self._owner()
        with self._lease(), self._scheduler() as scheduler:
            with scheduler._transaction():
                row = scheduler.db.execute('''SELECT r.state,j.action FROM scheduler_runs r
                    JOIN scheduler_jobs j ON j.profile_id=r.profile_id AND j.id=r.job_id
                    WHERE r.operation_id=? AND r.profile_id=?''', (operation_id, self.profiles.profile_id)).fetchone()
                if row is None or row['state'] != 'uncertain' or row['action'] not in ACTIONS:
                    raise AutomationError('automation_read_only_review_not_applicable')
                scheduler.db.execute("UPDATE scheduler_runs SET state='failed',result=? WHERE operation_id=?",
                    ('{"reason":"owner_reviewed_read_only_outcome_no_replay"}', operation_id))
                scheduler.db.execute("UPDATE automation_notifications SET state='denied' WHERE profile_id=? AND operation_id=? AND state='pending'",
                    (self.profiles.profile_id, operation_id))
        return {'reviewed': True, 'replayed': False, 'enabled': False}

    def stop(self):
        """Explicit owner Stop disables schedules and asks active work to cancel."""
        self._stopping.set()
        with self._scheduler() as scheduler:
            ids = scheduler.db.execute('SELECT id FROM scheduler_jobs WHERE profile_id=?', (self.profiles.profile_id,)).fetchall()
            for row in ids:
                with scheduler._transaction():
                    scheduler.cancel_in_transaction(row['id'])
                    scheduler.db.execute("UPDATE automation_notifications SET state='denied' WHERE profile_id=? AND job_id=? AND state='pending'", (self.profiles.profile_id, row['id']))
        return {'new_dispatch_stopped': True, 'active_read_may_finish': True}

    def request_shutdown(self):
        """Fast lifecycle barrier; idle saved schedules survive normal restart.

        A currently admitted check exits at its next safe boundary and its
        uncertain outcome still requires explicit owner review, never replay.
        """
        self._stopping.set()

    def serve(self, *, tick_seconds=30):
        """Optional managed service loop; constructor never calls this method."""
        if type(tick_seconds) is not int or not 1 <= tick_seconds <= 300:
            raise AutomationError('automation_tick_bounds')
        while not self._stopping.is_set():
            self.poll()
            self._stopping.wait(tick_seconds)

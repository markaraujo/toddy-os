"""Opt-in native Firefox launch and scoped read-only accessibility bridge.

Local reviewed HTML only. This is a fresh browser-profile boundary, not arbitrary
code confinement or a replacement for Bubblewrap plugin isolation. No HTTP fetch,
owner browser profile, cookie import, debug port, click/type or credential access.
"""
import hashlib
import json
import os
from pathlib import Path
import select
import signal
import stat
import subprocess
import tempfile
import threading
import time


class BrowserError(ValueError):
    pass


class BrowserSession:
    def __init__(self, *, firefox='/usr/bin/firefox', reader=None):
        # These are trusted installed-program bindings, never profile/page input.
        self.firefox = firefox
        self.reader = tuple(reader) if reader is not None else (
            '/usr/bin/python3', '-I', '-B', str(Path(__file__).with_name('atspi_read.py').resolve()))
        self._temporary = None
        self._browser = None
        self._reader = None
        self._url = None
        self._environment = None
        self._stopped = threading.Event()
        self._lock = threading.RLock()
        self._read_lock = threading.Lock()

    def launch(self, local_page, *, expected_sha256, authorize):
        with self._lock:
            if self._stopped.is_set():
                raise BrowserError('browser_stopped')
            if not authorize('browser.local.read'):
                raise BrowserError('browser_opt_in_required')
            if self._temporary is not None:
                raise BrowserError('browser_session_already_active')
            try:
                fd = os.open(local_page, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
                with os.fdopen(fd, 'rb') as stream:
                    metadata = os.fstat(stream.fileno())
                    if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1 or metadata.st_size > 65536:
                        raise BrowserError('browser_page_file_limit')
                    data = stream.read(65537)
                if len(data) > 65536 or hashlib.sha256(data).hexdigest() != expected_sha256:
                    raise BrowserError('browser_page_integrity')
                data.decode('utf-8', errors='strict')
            except (OSError, UnicodeError) as exc:
                raise BrowserError('browser_page_unavailable') from exc
            self._temporary = tempfile.TemporaryDirectory(prefix='toddy-browser-')
            root = Path(self._temporary.name)
            profile = root / 'profile'
            profile.mkdir(mode=0o700)
            (root / 'cache').mkdir(mode=0o700)
            (root / 'downloads').mkdir(mode=0o700)
            page = root / 'page.html'
            page.write_bytes(data)
            page.chmod(0o400)
            self._url = page.as_uri()
            preferences = {
                'accessibility.force_disabled': 0, 'browser.shell.checkDefaultBrowser': False,
                'browser.startup.homepage': 'about:blank', 'browser.startup.page': 0,
                'browser.sessionstore.resume_from_crash': False,
                'browser.download.dir': str(root / 'downloads'), 'browser.download.folderList': 2,
                'browser.download.useDownloadDir': True, 'browser.formfill.enable': False,
                'browser.newtabpage.enabled': False, 'signon.rememberSignons': False,
                'signon.autofillForms': False, 'identity.fxaccounts.enabled': False,
                'network.prefetch-next': False, 'network.dns.disablePrefetch': True,
                'datareporting.healthreport.uploadEnabled': False,
                'toolkit.telemetry.enabled': False, 'remote.enabled': False,
                'devtools.debugger.remote-enabled': False, 'extensions.autoDisableScopes': 15,
            }
            (profile / 'user.js').write_text(''.join('user_pref(' + json.dumps(key) + ', ' + json.dumps(value) + ');\n' for key, value in sorted(preferences.items())))
            env = {key: os.environ[key] for key in ('DISPLAY', 'WAYLAND_DISPLAY', 'XDG_RUNTIME_DIR', 'DBUS_SESSION_BUS_ADDRESS', 'LANG', 'LC_ALL') if key in os.environ}
            env.update({'HOME': str(root), 'XDG_CONFIG_HOME': str(root / 'config'),
                'XDG_CACHE_HOME': str(root / 'cache'), 'XDG_DATA_HOME': str(root / 'data'),
                'PATH': '/usr/bin:/bin', 'MOZ_NO_REMOTE': '1', 'MOZ_ENABLE_WAYLAND': '1'})
            self._environment = env
            try:
                self._browser = subprocess.Popen([self.firefox, '--no-remote', '--new-instance',
                    '--profile', str(profile), self._url], env=env, stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, close_fds=True, start_new_session=True)
            except OSError as exc:
                self._temporary.cleanup()
                self._temporary = None
                raise BrowserError('browser_launch_unavailable') from exc
            return {'browser_pid': self._browser.pid, 'url': self._url,
                    'fresh_profile': True, 'accessibility_read': 'pending'}

    def _attempt(self,pid,url,deadline):
        process=None
        try:
            with self._lock:
                if self._stopped.is_set():raise BrowserError('browser_stopped')
                try:
                    process=subprocess.Popen([*self.reader,str(pid),url],env=self._environment,
                        stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,
                        close_fds=True,start_new_session=True,bufsize=0)
                except OSError as exc:raise BrowserError('browser_accessibility_worker_unavailable') from exc
                self._reader=process
            output=bytearray()
            while True:
                if self._stopped.is_set():raise BrowserError('browser_stopped')
                if time.monotonic()>=deadline:raise BrowserError('browser_accessibility_timeout')
                if not select.select([process.stdout],[],[],.02)[0]:continue
                chunk=os.read(process.stdout.fileno(),4096)
                if not chunk:break
                output.extend(chunk)
                if len(output)>256*1024:raise BrowserError('browser_accessibility_output_limit')
            process.wait(timeout=max(.01,deadline-time.monotonic()))
            if process.returncode:
                try:error=json.loads(output.decode('utf-8',errors='strict'))
                except (ValueError,UnicodeError):error=None
                if process.returncode==2 and error=={'error':'browser_document_not_ready'}:
                    raise BrowserError('browser_document_not_ready')
                raise BrowserError('browser_scoped_accessibility_unavailable')
            try:return json.loads(output.decode('utf-8',errors='strict'))
            except (ValueError,UnicodeError) as exc:raise BrowserError('browser_accessibility_invalid_result') from exc
        finally:
            if process is not None:
                self._terminate(process);process.stdout.close()
            with self._lock:self._reader=None

    def read(self, *, authorize, timeout=3):
        if isinstance(timeout,bool) or not isinstance(timeout,(int,float)) or not .05<=timeout<=10:
            raise BrowserError('browser_deadline')
        if not self._read_lock.acquire(blocking=False):raise BrowserError('browser_read_busy')
        try:
            with self._lock:
                if not authorize('browser.local.read'):
                    self.stop();raise BrowserError('browser_current_authorization_required')
                if self._stopped.is_set() or self._browser is None or self._browser.poll() is not None:
                    raise BrowserError('browser_not_running')
                pid,url=self._browser.pid,self._url
            deadline=time.monotonic()+timeout
            while True:
                if not authorize('browser.local.read'):
                    self.stop();raise BrowserError('browser_current_authorization_required')
                try:result=self._attempt(pid,url,deadline)
                except BrowserError as exc:
                    if str(exc)!='browser_document_not_ready':raise
                    if self._stopped.wait(.05):raise BrowserError('browser_stopped')
                    if time.monotonic()>=deadline:raise BrowserError('browser_accessibility_timeout')
                    continue
                break
            if not isinstance(result,dict) or set(result)!={'untrusted','browser_pid','url','text'} or result['untrusted'] is not True or type(result['browser_pid']) is not int or result['browser_pid']!=pid or result['url']!=url or not isinstance(result['text'],str):
                raise BrowserError('browser_accessibility_scope')
            try:
                if len(result['text'].encode('utf-8',errors='strict'))>32768:
                    raise BrowserError('browser_accessibility_text_limit')
            except UnicodeError as exc:raise BrowserError('browser_accessibility_invalid_result') from exc
            with self._lock:
                if self._stopped.is_set() or self._browser.poll() is not None:raise BrowserError('browser_stopped')
                if not authorize('browser.local.read'):
                    self.stop();raise BrowserError('browser_current_authorization_required')
            return result
        finally:self._read_lock.release()

    def _terminate(self, process):
        if process.poll() is None:
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            try:
                process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                try:
                    process.wait(timeout=1)
                except subprocess.TimeoutExpired as exc:
                    raise BrowserError('browser_stop_uncertain') from exc

    def request_stop(self):
        """Fast cancellation barrier; worker finally owns bounded reap/cleanup.

        A stopped instance cannot clear this barrier by a queued launch. New
        explicit browser work creates a fresh BrowserSession instead.
        """
        self._stopped.set()
        with self._lock:
            for process in (self._reader,self._browser):
                if process is not None and process.poll() is None:
                    try:os.killpg(process.pid,signal.SIGTERM)
                    except ProcessLookupError:pass

    def stop(self):
        with self._lock:
            self._stopped.set()
            for process in (self._reader, self._browser):
                if process is not None:
                    self._terminate(process)
            self._browser = None
            if self._temporary is not None:
                self._temporary.cleanup()
                self._temporary = None
            return {'stopped': True, 'private_profile_removed': True}

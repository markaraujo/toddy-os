"""Credential work off the GTK main loop; callback receives fixed status/ref only."""
from concurrent.futures import ThreadPoolExecutor

from ..connections.secret_store import CredentialError,ProtectedStore


class CredentialsClient:
    def __init__(self,changed,*,store=None,schedule=None):
        self.changed=changed
        self.store=store or ProtectedStore()
        if schedule is None:
            from gi.repository import GLib
            schedule=GLib.idle_add
        self.schedule=schedule
        self.pool=ThreadPoolExecutor(max_workers=1,thread_name_prefix='toddy-credentials')
        self.busy=False
        self.closed=False
        self.generation=0

    def _request(self,method,arguments,connection_ref,success):
        if self.busy or self.closed:
            raise CredentialError('credential_store_busy')
        self.busy=True
        generation=self.generation
        def work():
            try:
                getattr(self.store,method)(*arguments)
                status=success
            except CredentialError as exc:
                status=str(exc)
            except Exception:
                status='credential_store_unavailable'
            # Completion contains no password or raw provider/service error.
            self.schedule(done,status)
        def done(status):
            if generation==self.generation and not self.closed:
                self.busy=False
                self.changed(status,connection_ref if status in ('credential_saved','credential_removed') else None)
            return False
        self.pool.submit(work)

    def save(self,profile_id,connection_ref,adapter_id,secret):
        self._request('save',(profile_id,connection_ref,adapter_id,secret),connection_ref,'credential_saved')

    def remove(self,profile_id,connection_ref,adapter_id):
        self._request('remove',(profile_id,connection_ref,adapter_id),connection_ref,'credential_removed')

    def close(self):
        self.closed=True
        self.generation+=1
        self.store.cancel()
        self.pool.shutdown(wait=False,cancel_futures=True)

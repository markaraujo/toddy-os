"""Protected-store policy fixtures only; never read/write the user's keyring."""
from concurrent.futures import ThreadPoolExecutor
import threading
import unittest
from unittest import mock

from runtime.connections.secret_store import CredentialError,LibsecretBackend,ProtectedStore,attributes
from runtime.ui.credentials import CredentialsClient


class FakeStore:
    def __init__(self):
        self.values={}
        self.locked=False
        self.available=True
        self.canceled=False
    def probe(self):
        if self.canceled: raise CredentialError('credential_canceled')
        if not self.available: raise CredentialError('credential_store_unavailable')
        if self.locked: raise CredentialError('credential_store_locked')
        return True
    def save(self,attrs,secret):
        self.probe()
        self.values[tuple(sorted(attrs.items()))]=secret
        return True
    def lookup(self,attrs):
        self.probe()
        try: return self.values[tuple(sorted(attrs.items()))]
        except KeyError: raise CredentialError('credential_missing') from None
    def remove(self,attrs):
        self.probe()
        return self.values.pop(tuple(sorted(attrs.items())),None) is not None
    def cancel(self): self.canceled=True


class CredentialTests(unittest.TestCase):
    def setUp(self):
        self.backend=FakeStore()
        self.store=ProtectedStore(self.backend)
        self.args=('profile-a','connection-a','openai')

    def test_secret_attributes_exclude_secret_and_profiles_and_adapters_do_not_share_items(self):
        self.store.save(*self.args,'dummy-key-not-real')
        self.assertEqual(self.store.lookup(*self.args),'dummy-key-not-real')
        self.assertNotIn('dummy-key-not-real',repr(attributes(*self.args)))
        for args in [('profile-b','connection-a','openai'),('profile-a','connection-a','anthropic')]:
            with self.assertRaisesRegex(CredentialError,'credential_missing'):
                self.store.lookup(*args)
        self.assertTrue(self.store.remove(*self.args))
        with self.assertRaisesRegex(CredentialError,'credential_missing'):
            self.store.lookup(*self.args)

    def test_locked_missing_and_unexpected_store_errors_never_fallback_or_leak(self):
        for state in ['locked','missing','error']:
            backend=FakeStore()
            if state=='locked': backend.locked=True
            elif state=='missing': backend.available=False
            else: backend.save=mock.Mock(side_effect=RuntimeError('dummy-key-not-real'))
            store=ProtectedStore(backend)
            with self.subTest(state=state),self.assertRaises(CredentialError) as result:
                store.save(*self.args,'dummy-key-not-real')
            self.assertNotIn('dummy-key-not-real',str(result.exception))
            self.assertEqual(backend.values,{})

    def test_malformed_refs_credentials_and_cancel_refuse_new_store_work(self):
        for secret in ['', 'contains spaces', 'line\nkey', 'x'*4097]:
            with self.assertRaisesRegex(CredentialError,'invalid_credential'):
                self.store.save(*self.args,secret)
        for reference in ['../key','https://private.invalid/key','x'*81]:
            with self.assertRaisesRegex(CredentialError,'invalid_connection_reference'):
                self.store.save('profile-a',reference,'openai','dummy')
        self.store.cancel()
        with self.assertRaisesRegex(CredentialError,'credential_canceled'):
            self.store.save(*self.args,'dummy')
        self.assertEqual(self.backend.values,{})

    def test_ui_completion_omits_secret_and_invalidates_callbacks_after_close(self):
        results=[]
        ready=threading.Event()
        queue=[]
        def schedule(callback,*args):
            queue.append((callback,args))
            ready.set()
        client=CredentialsClient(lambda *args:results.append(args),store=self.store,schedule=schedule)
        client.save(*self.args,'dummy-key-not-real')
        self.assertTrue(ready.wait(2))
        callback,args=queue.pop()
        callback(*args)
        self.assertEqual(results,[('credential_saved','connection-a')])
        self.assertNotIn('dummy-key-not-real',repr(results))
        client.close()
        self.assertTrue(self.backend.canceled)
        with self.assertRaisesRegex(CredentialError,'credential_store_busy'):
            client.save(*self.args,'dummy')

    def test_libsecret_request_deadline_is_bound_to_its_own_cancellable(self):
        backend=FakeStore()
        request=mock.Mock()
        request.is_cancelled.return_value=False
        backend.begin_request=lambda:request
        store=ProtectedStore(backend)
        with mock.patch('runtime.connections.secret_store.threading.Timer') as timer:
            self.assertTrue(store.save(*self.args,'dummy'))
        self.assertEqual(timer.call_args.args[0],2.0)
        self.assertEqual(timer.call_args.args[1],request.cancel)
        timer.return_value.start.assert_called_once()
        timer.return_value.cancel.assert_called_once()
        request.is_cancelled.return_value=True
        with mock.patch('runtime.connections.secret_store.threading.Timer'):
            with self.assertRaisesRegex(CredentialError,'credential_store_unavailable'):
                store.lookup(*self.args)

    def test_libsecret_lookup_never_requests_unlock_and_rejects_ambiguous_items(self):
        # Exercise actual adapter selection logic with a synthetic libsecret API.
        backend=LibsecretBackend.__new__(LibsecretBackend)
        backend.schema=object()
        backend.cancellable=object()
        flags=type('Flags',(),{'ALL':2,'LOAD_SECRETS':8,'UNLOCK':4})
        backend.Secret=type('Secret',(),{'SearchFlags':flags})
        collection=mock.Mock()
        collection.get_locked.return_value=False
        collection.get_object_path.return_value='/collection/default'
        item=mock.Mock()
        item.get_locked.return_value=False
        item.get_object_path.return_value='/collection/default/item'
        item.get_secret.return_value.get_text.return_value='dummy-key-not-real'
        service=mock.Mock()
        service.search_sync.return_value=[item]
        backend._context=lambda:(service,collection)
        self.assertEqual(backend.lookup(attributes(*self.args)),'dummy-key-not-real')
        self.assertEqual(service.search_sync.call_args.args[2],2|8)
        self.assertEqual(service.search_sync.call_args.args[2]&4,0)
        service.search_sync.return_value=[item,item]
        with self.assertRaisesRegex(CredentialError,'ambiguous_connection_reference'):
            backend.lookup(attributes(*self.args))
        service.search_sync.return_value=[item]
        item.get_locked.return_value=True
        with self.assertRaisesRegex(CredentialError,'credential_store_locked'):
            backend.lookup(attributes(*self.args))


if __name__=='__main__': unittest.main()

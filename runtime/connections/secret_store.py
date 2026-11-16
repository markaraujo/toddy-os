"""Protected per-user connection secrets; no file/log/environment fallback.

Synchronous entry points are for a worker thread. GUI callers must marshal their
completion onto the main loop. This module imports no GTK, model or root policy.
"""
import os
import re

IDS = re.compile(r'[a-zA-Z0-9_-]{1,80}\Z')
ADAPTERS = {'openai','anthropic','openrouter','openai-compatible'}
SCHEMA_NAME = 'io.github.markaraujo.Toddy.Connection'


class CredentialError(ValueError):
    """A fixed public code; raw service errors and credential bytes stay private."""


def attributes(profile_id, connection_ref, adapter_id):
    if not all(isinstance(value,str) and IDS.fullmatch(value)
               for value in (profile_id,connection_ref)) or not isinstance(adapter_id,str) or adapter_id not in ADAPTERS:
        raise CredentialError('invalid_connection_reference')
    return {'profile_id':profile_id,'connection_ref':connection_ref,'adapter_id':adapter_id}


def _credential(value):
    if not isinstance(value,str) or not 0<len(value)<=4096 or \
            any(not 0x21<=ord(char)<=0x7e for char in value):
        raise CredentialError('invalid_credential')
    return value


class LibsecretBackend:
    def __init__(self):
        try:
            import gi
            gi.require_version('Secret','1')
            from gi.repository import Gio, GLib, Secret
        except (ImportError,ValueError):
            raise CredentialError('credential_store_unavailable') from None
        self.Secret,self.Gio,self.GLib=Secret,Gio,GLib
        self.cancellable=Gio.Cancellable()
        self.schema=Secret.Schema.new(SCHEMA_NAME,Secret.SchemaFlags.NONE,
            {key:Secret.SchemaAttributeType.STRING for key in ('profile_id','connection_ref','adapter_id')})

    def cancel(self):
        self.cancellable.cancel()

    def _context(self):
        if os.getuid()==0 or os.geteuid()==0:
            raise CredentialError('unprivileged_connection_required')
        Secret=self.Secret
        service=Secret.Service.get_sync(Secret.ServiceFlags.OPEN_SESSION|Secret.ServiceFlags.LOAD_COLLECTIONS,self.cancellable)
        if service is None or not service.get_name_owner():
            raise CredentialError('credential_store_unavailable')
        # Bind the actual unique bus owner to this account; a caller-provided UID
        # or an imported profile never authenticates a secret service.
        uid=service.get_connection().call_sync('org.freedesktop.DBus','/org/freedesktop/DBus',
            'org.freedesktop.DBus','GetConnectionUnixUser',
            self.GLib.Variant('(s)',(service.get_name_owner(),)),self.GLib.VariantType('(u)'),
            self.Gio.DBusCallFlags.NO_AUTO_START,3000,self.cancellable).unpack()[0]
        if uid!=os.getuid():
            raise CredentialError('credential_store_owner')
        collection=Secret.Collection.for_alias_sync(service,Secret.COLLECTION_DEFAULT,
                                                    Secret.CollectionFlags.NONE,self.cancellable)
        if collection is None:
            raise CredentialError('credential_store_unavailable')
        if collection.get_locked():
            raise CredentialError('credential_store_locked')
        return service,collection

    def probe(self):
        self._context()
        return True

    def save(self,attrs,secret):
        _,collection=self._context()
        value=self.Secret.Value.new(secret,-1,'text/plain; charset=utf-8')
        item=self.Secret.Item.create_sync(collection,self.schema,attrs,
            'Toddy provider credential',value,self.Secret.ItemCreateFlags.REPLACE,self.cancellable)
        if item is None or item.get_locked() or collection.get_locked():
            raise CredentialError('credential_store_locked')
        return True

    def _items(self,attrs):
        service,collection=self._context()
        # No UNLOCK flag: a locked/missing keyring is never replaced by a file,
        # environment variable, imported value or an implicitly unlocked lookup.
        items=service.search_sync(self.schema,attrs,
            self.Secret.SearchFlags.ALL|self.Secret.SearchFlags.LOAD_SECRETS,self.cancellable)
        prefix=collection.get_object_path()+'/'
        if collection.get_locked() or any(item.get_locked() for item in items):
            raise CredentialError('credential_store_locked')
        if any(not item.get_object_path().startswith(prefix) for item in items):
            raise CredentialError('credential_collection_mismatch')
        if len(items)>1:
            raise CredentialError('ambiguous_connection_reference')
        return items

    def lookup(self,attrs):
        items=self._items(attrs)
        if not items:
            raise CredentialError('credential_missing')
        value=items[0].get_secret()
        if value is None:
            raise CredentialError('credential_store_locked')
        return _credential(value.get_text())

    def remove(self,attrs):
        items=self._items(attrs)
        return bool(items and items[0].delete_sync(self.cancellable))


class ProtectedStore:
    def __init__(self,backend=None):
        self.backend=backend
        self.canceled=False

    def cancel(self):
        self.canceled=True
        if self.backend is not None and hasattr(self.backend,'cancel'):
            self.backend.cancel()

    def _invoke(self,method,*args):
        try:
            if self.canceled:
                raise CredentialError('credential_canceled')
            if self.backend is None:
                self.backend=LibsecretBackend()
            if self.canceled:
                if hasattr(self.backend,'cancel'):
                    self.backend.cancel()
                raise CredentialError('credential_canceled')
            return getattr(self.backend,method)(*args)
        except CredentialError:
            raise
        except Exception:
            # GError messages can contain raw service data. Export codes only.
            raise CredentialError('credential_store_unavailable') from None

    def probe(self):
        return self._invoke('probe')

    def save(self,profile_id,connection_ref,adapter_id,secret):
        attrs=attributes(profile_id,connection_ref,adapter_id)
        return self._invoke('save',attrs,_credential(secret))

    def lookup(self,profile_id,connection_ref,adapter_id):
        attrs=attributes(profile_id,connection_ref,adapter_id)
        return _credential(self._invoke('lookup',attrs))

    def remove(self,profile_id,connection_ref,adapter_id):
        return self._invoke('remove',attributes(profile_id,connection_ref,adapter_id))


def lookup(profile_id,connection_ref,adapter_id):
    """Broker worker API: return only the protected secret, or a fixed error code."""
    return ProtectedStore().lookup(profile_id,connection_ref,adapter_id)

# Protected provider credentials

`secret_store.py` supplies a libsecret-backed per-user credential store shared by
native settings and the optional broker. It imports no GTK/model/executor and
loads the Secret typelib only when a protected-store operation is requested.
Missing libsecret/keyring support therefore does not break deferred/offline setup.
No environment/file/plain-text fallback, credential export or provider activation
is implemented.

Worker-thread interface:

```python
from runtime.connections.secret_store import ProtectedStore, lookup
store = ProtectedStore()
store.save(profile_id, connection_ref, adapter_id, credential)
credential = lookup(profile_id, connection_ref, adapter_id)
store.remove(profile_id, connection_ref, adapter_id)
```

Installed packages use the equivalent `toddy.connections` namespace. References
are opaque ASCII IDs of at most80 characters, scoped to the profile and adapter.
Supported adapter IDs are openai/anthropic/openrouter/openai-compatible. Credential
values are bounded printable ASCII matching the existing provider adapter contract.
Endpoint/model settings remain separate non-secret connection metadata; a key is
never a schema attribute, profile field, command argument, status signal or log.
The schema is `io.github.markaraujo.Toddy.Connection` with three non-secret
attributes: profile_id, connection_ref, adapter_id.

The actual unique secret-service bus owner must belong to the current unprivileged
account. Its existing default collection must be present and unlocked. Lookup
uses `ALL|LOAD_SECRETS`, never `UNLOCK`; locked, missing, ambiguous or wrong-collection
items fail with fixed error codes. Saving uses the explicitly checked collection
and replacement of matching schema attributes. There is no creation of an insecure
replacement collection. A collection locking during a write can yield a canceled
or unknown result; inspect through the protected store before assuming a retry is
necessary. Cancellation is best effort if the secret service already committed.

`runtime/ui/credentials.py` runs operations off the GTK main loop and sends only
a fixed status and opaque reference back to it. Closing cancels further work and
invalidates completion callbacks. The native password entry is masked, bounds
input, disables undo and clears immediately on Save/Remove/close. Python strings
and libsecret may hold transient in-process copies; this is not a claim of
cryptographic memory erasure. Any same-UID application with access to an unlocked
secret service remains within that account's trust boundary. B10 plugin isolation
must deny that access separately.

API source: official [libsecret API1 Python examples](https://gnome.pages.gitlab.gnome.org/libsecret/libsecret-python-examples.html)
and [Service.search](https://gnome.pages.gitlab.gnome.org/libsecret/method.Service.search.html),
rendered upstream documentation version0.21.8.2, inspected2026-11-16. Exact native
libsecret/gnome-keyring packaging remains the accepted B02 target's responsibility;
no library version is changed by this source adapter.

Checks use a synthetic protected-store API and dummy strings only. No real user's
keyring item was read/written. Native S12 still requires actual per-user dummy-key
store/read/delete, another-user denial, locked/missing collection failure and
absence from exports/logs before protected credential setup can be accepted.

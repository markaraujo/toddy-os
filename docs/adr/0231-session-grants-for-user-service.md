# ADR-0231: Bind background broker grants to the owner's active local session

Date: 2026-11-16. Status: implementation; affected native proof pending.

Review of B05 integration found that a user-systemd broker belongs to the per-user
manager, not necessarily the originating GUI logind session. Trusting a broker-
supplied session ID would allow untrusted transport data to select authority;
using standing grants as an automatic fallback would change owner intent.

A session grant applies to the account only while its exact selected owner
session remains active, local and unlocked. The root executor resolves UID/PID
from the system bus. If logind identifies the sender's session, that session must
match User, Active, Remote and LockedHint checks. An existing inactive/remote/
locked session never falls back to another session. Only logind's exact
NoSessionForPID response allows the executor to resolve that same UID's User.Display
and validate those same properties. Bus errors and missing metadata deny session
authority. No PID/session/grant field is added to model/broker requests.

The durable grant retains its original session ID. Logout, lock, display-session
replacement or remote callers cannot silently become standing authorization.
Standing grants preserve their deliberate account scope/expiry/revocation. As
before, arbitrary hostile same-UID code is not a separate profile-secret boundary.
A user who grants full account administration authorizes the account's background
broker while the granted interactive session is usable; revocation remains root-
enforced independently of conversation and tool output.

Source: native Systemd261.2/logind and the existing authenticated B04 identity
boundary. The [pam_systemd reference](https://www.freedesktop.org/software/systemd/man/latest/pam_systemd.html)
explains PAM-created session scopes and per-user manager distinction (reviewed
2026-11-16). Existing GDM login evidence is reused; this change requires the
changed active-session/blocked-after-logout native IPC cases and root control
regressions. Host metadata tests alone do not accept the transport behavior.

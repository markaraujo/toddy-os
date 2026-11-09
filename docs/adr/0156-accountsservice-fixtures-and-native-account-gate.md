# ADR0156: AccountsService fixtures and real native account gate

Status: fixture stage qualified; real native account gate pending, 2026-11-09.

Frozen AccountsService26.27.3 meson.build162 requires JSON-C>=0.15 even when
create_homed=false. The book's paragraph omits that dependency; JSON-C0.19 already
belongs to the selected frozen graph. Its shared library is now owned after28
original programs (27reused/one repaired CLI fixture) and actual strict
UTF8/depth/refusal/recovery checks. No foundation version replacement.

AccountsService's published source derives its release version from the tarball
basename. Copy authenticated read-only input into a private correctly named
worker directory; no fake Git metadata. Reuse its two bundled SHA-locked mocklibc
archives and exact upstream diff with nodownload fallback. No test helper enters
the runtime stage. Original14programs passed; four daemon fixtures initially
aborted because the synthetic namespace lacked machine-id. Add only an input-
specific synthetic read-only ID, never a real host/target ID. Three cases passed;
the remaining case needed en_IE locale data. Generate only private LOCPATH data
using qualified glibc2.44 localedef. All original assertions remain unchanged;
log-only teardown instrumentation preserves evidence before upstream cleanup.
Reuse14programs/three repaired cases, rerun only the locale case;27ELFs unchanged.
[Staged fixture proof](../evidence/B02-accountsservice-stage.json).

These mocks do not qualify real account administration. Before owned promotion,
boot a new disposable native child and use the actual system bus, installed
Polkit/PAM/Shadow, upstream service unit/hardening and real temporary users.
Check own-user update and actual passwd effect, cross-user name/password refusal,
protected shadow-file icon-read refusal, root-authorized password update and real
PAM new/old password checks, Stop, new daemon owner/reconnect and persistence.
Verify source/stage/client bytes unchanged and remove ephemeral accounts.

Source review: caller identity comes from D-Bus peer credentials, actions separate
own data from administration; user_change_password_authorized_cb sends encrypted
input to chpasswd-e through stdin and logs only user identity. No password/hash
in command arguments, logs or evidence. Optional homed remains unavailable; no
GDM/graphical/physical acceptance follows from fixtures or this service gate.

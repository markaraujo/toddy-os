# ADR0156: AccountsService fixtures and real native account gate

Status: fixtures and real native account gate qualified; owned package installed, 2026-11-09.

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

Native attempt1 started actual daemon and reached protected-icon refusal but
its message classifier rejected upstream's generic `reading file ... failed`
message. Preserve failure; source user.c maps the helper's failed read to this
message. Accept only that exact protected path or permission diagnostic, retain
remote-error/no-icon-effect assertions and add direct same-peer EACCES proof.
Use a fresh disposable context2; no runtime source/security change or rebuild.

Fresh native context2 passed10real outcomes,94fixture files unchanged, accounts
removed, no secrets retained. Child stopped0/OOMfalse and backing identity checked
before restart. Source-bound receipt accepted once; controlled owned promotion
26.27.3-1+toddy1 recipe/post0/0 changed111paths, CLI/GI/SDK/audit0.
[Native](../evidence/B02-accountsservice-native.json),
[installation](../evidence/B02-accountsservice-install.json). GDM/GUI remains pending.

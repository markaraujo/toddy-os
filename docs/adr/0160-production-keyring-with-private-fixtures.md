# ADR0160: Production Keyring without test hooks

Status: production package owned; native PAM/GNOME integration pending, 2026-11-09.

Frozen GNOME Keyring50.0 source requires Gcr3/Gck1 (ADR0159) and builds a PAM
module for the planned login. Build production with debug-mode=false; supported
optional SSH-agent, libcap-ng and SELinux features are disabled. Apply only the
frozen book's /desktop to /org schema path correction recorded during preparation.
No login policy is enabled by this package transaction.

The first production job compiled successfully and passed57original programs.
Five D-Bus fixtures timed out because they require WITH_DEBUG-only custom service,
login and prompter environment hooks: daemon/dbus/gkd-dbus-secrets.c and gkd-dbus.c.
Increasing timeouts cannot supply hooks deliberately absent from production.
Preserve the failures; never count timeouts as passes or enable test hooks in the
installed daemon. Build one separate private debug-only daemon and run ONLY those
five original programs on private buses. All five passed without skips; the
fixture daemon is never staged. All332production ELF files stayed unchanged.

The unchanged production daemon reports testing:disabled, stages113regular files,
and its actual PAM module loads all five expected entry points. A separate actual
production Secret Service probe uses SecretTool and a real private bus, with no
mock/test-hook environment, on the isolated unprivileged builder kernel. Six
outcomes passed: create/store/client lookup; no plaintext password/value in private
storage and0600keyring; lock/refused actual GetSecret; clean Stop/bus removal;
wrong-master restart remains locked; correct-master restart preserves value and
acquires a distinct owner. Synthetic random values are supplied only through
pipes and removed with their private data; only output digests are retained.
This proves the isolated backend, not native GNOME/PAM login, permission prompts,
GUI focus or physical hardware. Those remain B02 integration gates.

Promotion binds the original source/recipe hashes, successful helper command code,
original test records, production artifacts and backend report before the guarded
native package transaction. Install/post0/0 changed129root paths. The parent PAM
policy is unchanged; schema cache union remains a controlled separate transaction.
No fixture password, owner credential, ciphertext, private SDK or test-hook daemon
is shipped. Preserve original failed jobs and reuse unchanged passed evidence.

[Keyring evidence](../evidence/B02-gnome-keyring-install.json).

# ADR0153: Qualify the exact Polkit privileged profile in a disposable guest

Status: selected native test profile, installation pending, 2026-11-09.

Polkit127 with ADR0151 passed all five original native test programs (59observed
TAP cases). The backend suite uses mock bus fixtures; it does not qualify actual
system authorization or PAM. Preserve it unchanged and run a separate native
disposable-overlay privilege gate before owned package promotion.

The upstream Meson post-install script requests root:root4755 for pkexec and
polkit-agent-helper-1. Compiler staging remains0755/unprivileged. Test those exact
binaries only in a new native child with verified TODDY-BOOT-TEST disk identity:

- /usr/bin/pkexec SHA256303729b3ce4713fb0ea0554502ea7bb0c87eda38f4f09d501e6dc9f0f70a103a
- /usr/lib/polkit-1/polkit-agent-helper-1 SHA256112083c1da8ff12ac29563f97556b7141a36f0981f8b0e450ef504dbc7e0f73b

Use upstream daemon/systemd helper socket units and their existing hardening.
The daemon remains its own unprivileged sysusers account. Test-only rules choose
an ephemeral administrator; passwords are generated at runtime, fed over a real
controlling terminal, never retained in output/evidence. The temporary PAM include
uses required pam_unix auth/account, preserves the normal authentication delay and denies
password/session management groups. Neither this include nor test rules
constitutes installed owner policy. Preserve the generic privilege guard; any
later native package privilege exception must name these exact paths/hashes and
require successful real qualification first.

Require allow/deny/no-agent challenge, correct/wrong-password, cancellation during
authentication, recovery, distinct daemon bus identity after restart, and refusal
after policy revocation. Verify all479source/build/stage fixture files unchanged.
These are native VM results, not physical tests, a GNOME permission UI, a B04
completion, or an accepted installed package. A failure remains a failure.

The accepted Systemd profile has no systemd-sysusers helper. Initial native setup
failed before any authorization attempt. Use the already qualified Shadow useradd
for the isolated service account and apply the exact upstream tmpfiles directory
policy root:polkitd0750. No foundation rebuild or service hardening change. Keep
the declarative upstream sysusers/tmpfiles files for compatible future profiles.

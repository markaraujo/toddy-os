# ADR-0148: Qualify the frozen PAM helper before login integration

- Date: 2026-11-09
- Status: Native helper qualified and owned package installed; session integration pending

Linux-PAM1.7.2 with ADR0126's nine exact backports passed77original unprivileged
unit drivers and actual staged permit/deny/missing-module/malformed-policy/
recovery checks. Optional userdb/NIS/SELinux/audit/libeconf are disabled, not
qualified. Native password and session behavior cannot be inferred from these
unit checks.

Use a fresh disposable cold overlay of the current Toddy7.1.8/Systemd reference
guest, no NIC, with an authenticated immutable copy of the nonprivileged stage.
Enable only its exact unix_chkpwd helper as root:root4755 **inside that disposable
overlay**. BLFS13.1 postlfs/linux-pam.html (frozen page SHA256
341f6f23114e22d4a8a1f23b7664be1ecb9d6f53909afe1f1a22ed19e7fc4c26)
explicitly requires this mode. The binary links only the accepted libc/libcrypt
and loader; no staged PAM library search path enters its setuid loader.

Create one ephemeral user/yescrypt password at runtime, feed passwords only on
stdin and keep neither password nor hash in reports. Test correct/incorrect,
empty, unknown-user, locked-account, child-only NoNewPrivileges refusal and
unlock/recovery from the unprivileged user's identity. Remove the test account;
verify all fixture bytes remain unchanged. Never use an existing owner password.
No global host/builder security control is changed. The compiler stage remains
0755 and the generic stage privilege rejection remains intact.

A512MiB regular-file scratch filesystem on the disposable builder root contains
PAM compiler output without consuming the target16GiB reserve. Its exact UUID,
inode and mount receipt are mandatory for restoration; never recreate/reformat
an existing scratch image. Only the small frozen source/native fixture resides
on the designated target. Existing four volumes and accepted evidence are reused.

Passing this gate permits preparation of an explicit native package/helper
ownership exception. It does not prove GDM, Shadow's PAM integration, pam_systemd,
logind, a recoverable authenticated boot or B02 completion. Those gates remain
required, and the owner boundary remains complete ALL B02 then stop.

Actual native7.1.8 qualification passed all seven selected cases,157fixture files
unchanged, ephemeral account removed; report SHA256
28e4d9c1f7947a929c0d4d75c58677585c5de670c7c797b0d29f801850d5b5c6.
The child stopped0/OOMfalse and the source parent was unchanged before restart.
The package now explicitly owns only unix_chkpwd root:root4755 and a deny-all
other fallback policy. A prewrite missing-metadata refusal and then a wrong exact
Libxcrypt revision left the first archive unpacked/unconfigured; both failures
remain. A distinct metadata revision preserved all457payload entries and
configured successfully (recipe/post0/0, five root path changes). Actual installed
C/module/refusal/recovery and Dpkg/APT checks passed. No source/test replay. See
[installed proof](../evidence/B02-pam-install.json) and
[native credentials](../evidence/B02-pam-native-1.json).

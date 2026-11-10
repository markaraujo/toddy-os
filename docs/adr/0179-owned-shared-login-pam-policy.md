# ADR-0179: Additive owned shared login PAM policy

Status: policy package installed; actual native qualification pending.

Provide the four missing shared GDM includes in architecture-all
`toddy-login-policy0.1.0-1+toddy1`. Original Toddy configuration is MIT licensed;
PAM/Systemd modules keep their existing source licenses and package ownership.
Follow frozen BLFS13.1-systemd postlfs/linux-pam.html and general/systemd.html:
auth/account require pam_unix; password uses yescrypt/shadow/try_first_pass;
session requires pam_unix/pam_loginuid and includes optional pam_systemd. Optional
module status is not proof of logind integration: native tests must observe the
actual session, owned0700 runtime directory, user manager and real user bus.

Do not copy the book's illustrative nullok/other sample. All three existing
other/Polkit-auth/systemd-user policies retain exact bytes/modes/ownership. Existing
PAM/Systemd binaries and modules are not rebuilt/replaced. Each new file is an owned
conffile with explicit PAM1.7.2toddy2/Systemd261.2toddy3 dependencies. The package
adds no permissive fallback, helper capability, service activation or host policy.
The full-root runner remains in use for this unqualified configuration recipe.

Initial native dispatch failed before staging/receipt/archive and changed ZERO
root paths because the new config directory was absent from the explicit metadata
transfer allowlist. Declare that directory and project LICENSE in the existing
verified locked transfer. Check absence before a new native step; no uncertain
install replay. Install2/post0/0 changed15paths and owns14entries. The four policy
files and unchanged pre-existing policies/modules passed ownership/hash/audits.
This is installed configuration evidence, not authentication or login acceptance.
[Package and prepared fixture evidence](../evidence/B02-login-policy-install.json).

Reuse the two previously qualified password/session C clients by exact source/
binary hashes. Compile only one tiny root-only synthetic PAM password-change
client in a new read-only-input/unprivileged/no-route sandbox; its malformed-argc
invocation returns64 and performs no password operation. Native testing must also
prove proper-argc unprivileged refusal, not infer it from the argc guard. New
fixture binds three clients and14installed artifact/policy hashes. No password,
hash, signing material or owner credential enters its source, manifest or logs.

The actual gate uses a NEW disposable cold boot overlay of the current verified
backing, serial TODDY-BOOT-TEST, native kernel7.1.8, Systemd PID1 and no NIC. The
builder is stopped, its backing remains read-only and identity is verified after
child cleanup before recovery/restart. Never boot an old overlay after changes.
Use synthetic native user/yescrypt token via stdin only; test correct/wrong/empty/
missing/locked/expired-account outcomes and recovery; root PAM password change
plus old-token refusal/new-token recovery; proper-argc unprivileged change-client
refusal; PAMName Stop and two actual PAM/logind/user-bus cycles. Stop before token
submission is explicitly not in-flight PAM cancellation. Require actual exits and
postconditions, original policy/module hashes and cleanup. No timeout/log absence
is a pass. No GUI/GDM/keyring/physical acceptance is inferred from this gate.

Next integrate reviewed GDM account/sysusers/directories/conffiles/native package
and its actual PAM/keyring/greeter/login flow; preserve the independent owner policy
and native GNOME graphical requirements. No general plan or foundation rebuild.

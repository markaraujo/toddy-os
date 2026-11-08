# ADR0142 — Preserve builder security when nested namespace tests fail

Date: 2026-11-08. Status: accepted execution boundary; native runtime test pending.

## Context and evidence

Bubblewrap0.11.2 compiled in the disposable Ubuntu6.8 builder. Its original
utility program passed26cases. Three original shell drivers failed before
functional tests because their shared fixture hardcodes /var/tmp, absent from
our read-only compiler root. The optional Python seccomp driver skipped because
that binding is unavailable. These are not five passing drivers or sandbox
qualification. The unchanged standalone namespace consumer also failed EPERM.

The builder reports unprivileged_userns_clone1, max_user_namespaces47681 and
apparmor_restrict_unprivileged_userns1. Ubuntu documents per-application
AppArmor userns profiles as the supported alternative to global weakening:
[Ubuntu24.04 release notes](https://documentation.ubuntu.com/release-notes/24.04/)
and [AppArmor4.0 syntax](https://manpages.ubuntu.com/manpages/noble/man5/apparmor.d.5.html).
These facts motivated a scoped experiment; they do not prove the precise syscall
rejection cause in our nested compiler namespace.

A temporary profile attached only to the project bwrap path in this VM. First
attachment used chroot paths and the observed child remained unconfined. The
second used the root-owned private compiler root prefix and the child acquired
toddy-phase2-bwrap, but actual namespace creation still failed. An unprofiled
userns negative control remained denied. Both corrective attempts failed; no
NoNewPrivs/capability/network/read-only compiler guards were relaxed. The exact
profile was unloaded after proving no process used it, its file removed and the
global restriction verified still1. Host security was never changed.

## Decision and next action

Stop this diagnosis branch after two failed corrections. Preserve compiled
bwrap, all original test logs,26utility passes, optional-driver skip, denied
consumer results and the removed-profile receipt. Do not promote the package,
skip the image decoder sandbox, enable setuid or disable global restrictions.
Continue independent GNOME dependencies. Validate bwrap namespaces on the planned
native Toddy kernel/runtime before revisiting only the affected original drivers
and native consumer. The /var/tmp fixture also requires an explicit private
runtime path; neither absence nor skips count as successful sandbox acceptance.

No broader architecture or foundation rebuild is authorized by this blocker.

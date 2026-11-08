# ADR-0119: Durable executor Stop and command lifetime

Date: 2026-11-08 UTC. Status: accepted; installed-unit proof pending B04/B02.

CancelOperation authenticates the actual sender and owner-binds the operation.
An owner can stop already accepted work even after revoking further dispatch.
The independent SQLite record persists cancel_requested. A planned operation is
canceled before dispatch. An in-flight atomic configuration change checks before
commit; a completed safe commit is not undone. Root commands check cancellation
at bounded read/wait intervals, kill their owned process group and reap before
terminal recording. Never advertise canceled root writes as reversed.

If effects cannot be verified, preserve uncertain with the cancellation flag and
never replay the ID. A restart changes running to uncertain independently of the
conversational service. Existing B04 store files gain the cancel column without
losing IDs/results; native migration and actual process-loss tests passed.

A small fresh-interpreter launcher sets Linux PR_SET_PDEATHSIG(SIGKILL), checks
the expected parent after setting it and execs the command. It avoids preexec_fn
inside the threaded root service. Native executor-ipc-5 killed the actual service
after a root child wrote its marker; the child disappeared and restarted service
retained an uncertain operation. This does not constrain arbitrary root descendants:
fork/credential/set-ID/capability transitions can clear the parent-death setting,
and unrestricted root can deliberately escape any local constraint.

The packaged systemd unit therefore requires KillMode=control-group and normal
SIGKILL fallback for service lifecycle ownership. Frozen systemd261.2 source
man/systemd.kill.xml lines63-103 was read directly from its verified archive;
[upstream reference](https://www.freedesktop.org/software/systemd/man/latest/systemd.kill.html)
currently262 describes the same behavior (introduced187). The unit is staged
source, not an installed-systemd acceptance result. Actual unit/cgroup and logind/
polkit owner surface must be proved before B04 completion.

Linux [PR_SET_PDEATHSIG documentation](https://man7.org/linux/man-pages/man2/PR_SET_PDEATHSIG.2const.html)
(man-pages6.19, consulted2026-11-08) explains parent-thread semantics and clearing
conditions. Native proof ran the development guest6.8 kernel; final7.1.8 installed
image lifecycle validation remains required. No guarantee against authorized
unrestricted root or arbitrary account code is claimed.

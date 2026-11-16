# ADR-0232: Managed user-tool scopes and a verified dispatch gate

Date: 2026-11-16. Status: source and host proof; native integration pending.

B04's low-level ordinary argv tool used a process group and parent-death signal.
An arbitrary command can call setsid and escape that group. Root executor
systemd cgroup cleanup is qualified separately and does not prove ordinary Stop.

Production broker shell routing now requires a user-systemd transient scope.
The fixed parent unit must be active, MainPID must equal the broker and its
cgroup must match the calling process; otherwise shell stays unavailable. Scope
BindsTo/After bind its lifetime to toddy-agent.service. KillMode=control-group,
bounded stop timeout and runtime bound apply. A trusted isolated Python launcher
writes readiness before executing any user argv; the broker verifies actual PID/
UID/cgroup and current cancellation before opening its private dispatch gate.
A manager/registration failure has no uncontained fallback. No external unit name,
callback or systemd property is accepted from task JSON.

Stop/output/deadline cleanup stops the entire scope, kills only a still-owned
unreaped runner process group, stops once more for registration races and verifies
empty/absent cgroup. Cleanup uncertainty is an error, not successful Stop. Exit
and process cleanup do not prove or undo arbitrary file/network side effects;
canonical tasks retain uncertainty until independently verified.

The existing Tools.shell remains a low-level process primitive for its scoped
fixtures; production BrokerCore no longer selects it implicitly. This does not
restrict the separately authorized full-administration root executor.

Sources: [Systemd scope reference](https://freedesktop.org/software/systemd/man/latest/systemd.scope.html)
and [systemd-run reference](https://freedesktop.org/software/systemd/man/latest/systemd-run.html),
reviewed2026-11-16 for target Systemd261.2. Actual host-only test in a unique
project-owned transient user service passed an ordinary UID/output task and Stop
of a real detached setsid descendant. It changed no host service configuration or
other user unit. Native Systemd261/per-user broker/Stop/loss proof remains required;
no hardware/G2 claim. The source broker smoke without a systemd parent can no
longer qualify shell execution and must report this boundary truthfully.

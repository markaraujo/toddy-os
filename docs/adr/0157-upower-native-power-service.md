# ADR0157: frozen UPower Linux service and bounded native gate

Status: portable stage qualified; real service gate prepared, 2026-11-09.

Use frozen BLFS13.1-systemd UPower1.91.3, sourceSHA
12227b3dcd34c5097bbda25984b192ea0bd5e11dce479358d9ef70415a38e4b6,
book page89862aad0be36627e9dfaff40b317fa87f261b29b66b2c800836225dd140e18a.
Select actual Linux backend, installed Polkit127, introspection, no optional
libimobiledevice, docs or installed integration fixtures. Five original portable
backend/device/list/history/native cases pass; explicitly omitted system-bus
polkit/daemon cases are not passes. Optional Umockdev device matrix remains
unqualified, not simulated battery acceptance.

Initial actual build/stage succeeded; own CLI --version required a real system
bus even for version output (tools/up-tool.c318). Use early CLI help and actual GI
version constants/types/history for stage; preserve failure. Next consumer's
module-level method assumption was wrong: published GIR nests conversions under
Device. Structural diagnosis and exact corrected consumer passed; no compilation,
original test or stage replay, all prior ELF artifacts unchanged.

Power-service privilege review: upstream unit retains ProtectSystem=strict,
ProtectHome, NoNewPrivileges, empty capability bounding set, IPAddressDeny=any,
AF_UNIX/AF_NETLINK, PrivateUsers and syscall restrictions. The shipped rule allows
only subject.user==root to ignore logind inhibitors for five power actions; no
unprivileged or assistant policy grant. Do not weaken this unit/rule to pass tests.
Battery policy remains the upstream system service, independent of assistant policy.

Before promotion, fresh no-NIC native child must run the two omitted original
bus-dependent tests without skip text and query actual daemon/CLI1.91.3, observed
power state and device list, invalid-method refusal, Stop and distinct-owner
reconnect. Preserve hardening, no mock environment, unchanged39file fixture.
Never invoke suspend/hibernate/reboot/power-off for this slice; no physical power,
battery, iDevice or graphical settings acceptance is inferred.
[Stage](../evidence/B02-upower-stage.json).

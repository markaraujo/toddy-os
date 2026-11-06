# ADR-0058: Enable credential-free login only on the foundation live consoles

- Date: 2026-11-06
- Status: Native terminal chain and offline units verified; real boot pending

G1 requires actual login, not only a transient boot-test service. Fresh image
accounts from ADR-0055 retain a locked root password and no builder credentials.
For the experimental foundation live medium, use native Util-linux agetty
automatic login with native Shadow login on tty1 and ttyS0 only. The issue banner
states root access and volatile writes. A person with access to either live
console has administrative access to that live session. This is the foundation
rescue/development interface; the installed desktop needs its own owner account
and login policy, implemented and tested in Phase 2.

The prepared live_console.stage_console component writes two instance-specific
Systemd drop-ins, one issue file and the required enablement links into a fresh
image stage. It retains Systemd's existing canonical root-owned tty1 enablement
link. It never changes template units or passwords, creates an SSH service,
copies a password hash, or enables automatic login on other terminal instances.
Existing profile inputs, redirected parents, an unlocked root or a baked-in
runtime marker are refused before profile writes. The caller must enforce H10
prerequisites and record generated image files separately from package payload.

Both units require ConditionKernelCommandLine=toddy.live and
ConditionPathExists=/run/toddy/live-session. The prepared /init now requires the
explicit live boot parameter and writes this public runtime marker only after
media digest verification, overlay setup and ACL restoration. The marker resides
on the volatile /run mount carried through switch_root; it is absent from the
compressed root. These conditions prevent accidental automatic login from merely
copying the image profile to a non-live boot. They are not a security boundary
against someone who already controls root or the boot environment.

The future installer must explicitly exclude/remove the two live drop-ins and
issue file, generate ordinary installed login enablement, and verify login after
removing the ISO. Keeping these drop-ins without their live conditions would
prevent those instances from starting, so absence of automatic login alone is
not sufficient installed-system acceptance. Never relax their conditions to fix
an installed login failure. The desktop/PAM transition also requires revalidation;
this experiment covers the frozen non-PAM foundation, not future PAM behavior.

## Actual native checks

scripts/host/probe_live_console.py transfers public component source over stdin
without synchronizing the running H07 checkout. It creates a fresh guest root in
private PID/mount namespaces, a new devpts instance and fresh locked accounts.
All five programs and loader dependencies are checked against installed own
package records before copying. The login binary's actual mode is verified as
0755, matching its package record; no set-ID bit is stripped from that program
to manufacture the unprivileged refusal. The native login.defs also matches its
own source-built package record.

Source-built Systemd 261.2 systemd-analyze verify reads the two drop-ins together
with the real native unit templates/dependencies and exits 0 without diagnostics.
Each drop-in's actual ExecStart command is then run in its own private terminal:
both native agetty -> Shadow login -> login Bash sessions report UID/EUID 0,
HOME=/root and shell=-bash, execute id, and exit 0. The serial baud-options variant
is exercised on a PTY; real UART baud handling and actual tty1 activation are not
claimed. Normal password login rejects the public invalid probe input with
Login incorrect; the waiting retry session is then deliberately killed, exit -9.
Unprivileged login -f root exits 1 without a shell. Fixture account files remain
unchanged. Four refusal/preservation cases cover existing profile, baked marker,
redirected parent and unlocked root. Installed account files and Dpkg status
remain unchanged by hash. Namespace mounts and successful fixtures are removed
after retaining the report.

Complete report .local/logs/h10-live-console-probe.json SHA-256:
b8392bc45150740c661a86b7618e12287e7d7d3662f1f60339f05c94ff20a5e3.
Profile component SHA-256:
309a0f10c676a725708a56c54c876d0eabb96e9232777e97a2823dccf8345f03.
Updated /init SHA-256:
8f9bb8289983b3bed29a4371b206303700f325cab7d3bd7e97def6666dc4ffc2.
The changed /init also passed the complete native archive/extraction checks from
ADR-0054, including identical archives from two fresh stages and non-PID1 refusal.
Report SHA-256 ca14ba7840273387bc7d41daf1157558458ba0d0099bcd0b453f4041bea1bfb9.
The 44-entry archive contains 20 native files and is 14,271,309 compressed bytes;
gzip SHA-256 3c972a7873562fcaad872c07d3add10b459b9fdc254f1bad3c2edafdb5124cc0.
All reports retain immutable content-addressed copies outside Git.

## Sources, alternatives and remaining acceptance

Primary sources inspected directly are frozen LFS 13.1-systemd chapter08/shadow.html
(SHA-256 920af8c1417c5ef387eb13da4a6a6dfae6f569c2df3150e8f0ef729c57cc01cf),
chapter08/util-linux.html
(9265741e66efb44f59ebb02ba130de1ab348c1e4d8fde8e4dfa89b9149dc3ea9),
Shadow 4.20.2 src/login.c and lib/console.c, and Util-linux 2.42.4
term-utils/agetty.c and agetty.8.adoc. The latter version is the already frozen
security overlay from ADR-0013, not a new upgrade. Archive hashes:
Shadow b89f432b75ae55a2d852b446d0365484795fdf533ab97d550e325fa15594a224;
Util-linux fbd62a100ab7bb8746ba0661255c3c48185b1e9021507c624da01fbc696330ec.
Native Systemd getty@.service and serial-getty@.service provide the original
command forms and terminal ownership. Agetty supplies login's -f option;
Shadow's non-PAM preauthentication flow and actual execution establish behavior
with the fresh shadow lock. A comment about locked passwd entries is not treated
as proof of what the separate shadow entry does; the native probe is decisive.

Rejected alternatives: a shared live password embeds reusable credentials;
unlocking root globally changes authentication outside the two live units;
executing Bash directly bypasses the native login chain; modifying the shared
getty template broadens automatic login to unintended terminals.

Actual Systemd activation, marker handoff, console logout/restart, keyboard/serial
usability, BIOS/UEFI/virtual-USB boot and recovery remain H10/H12 obligations.
The builder kernel is 6.8.0-147-generic. No native Toddy kernel or ISO has booted,
and no H07/H10/G1 acceptance is inferred from these private component tests.

# ADR-0187: Park headless focus gate and separate native evidence transport

Status: third gate failed/incomplete; no new acceptance or unchanged native retry.

Native3 committedinput66d2d46 used the corrected late startup init hook, actual
registered synthetic PAM/logind user and owned Gst stack on a fresh no-NIC overlay.
The child exited0/OOMfalse. Console summary explicitly reports all_selectedfalse.
One of76report chunks (50) is missing: console contains only a truncated
TODDY_B02_RUNTIME_D line with python3 printk prefixes. The full report SHA cannot
be verified; do not accept this gate or silently manufacture a missing chunk.

A contiguous50chunk compressed prefix was decoded read-only for diagnostics only.
Its complete actions field records panel/monitor, overview open/close, quick settings,
panel focus and GTK window mapping, then actual-GTK-window-focusedfalse. These are
partial diagnostic observations, not accepted positive test results. Only one
complete PNG object could be separately recovered with its own original hash.
The overall report remains incomplete; no GDM/login/basic-app/focus pass.
[Original serial, exact missing index, partial diagnostic, image metadata and recovery](../evidence/B02-shell-third-native-incomplete.json).

This changes the next action: automation now reaches actions, while actual window
focus remains unqualified under headless input. Earlier headless Mutter scope also
never qualified focus. Do not force a focus flag, remove the failed assertion or
promise that a screenshot proves keyboard interaction. Park this branch after the
two unsuccessful corrective gate attempts and proceed with required apps. Concrete
unblock: a real virtual graphical seat/input (kernel fragment already selects
Virtio GPU/evdev/Virtio input; actual device/backend still needs measurement), or a
new source-backed focus cause, plus reliable complete evidence on a fresh overlay.
Do not rebuild the accepted foundation or replay the prior headless inputs.

Prepare only a transport correction for the next eligible native probe: use a second
virtual serial UART, as supported by existing native-regression infrastructure,
separate from kernel/getty/journal console. The fixture sets this private virtual
port to115200raw, writes exact existing bounded chunk/full-report SHA protocol and
drains it before shutdown. Controller decodes ONLY native-evidence.log and records
its SHA; console remains diagnostic. No weaker verifier/fallback acceptance, global
security change, physical serial access or automatic native retry. Runtime validation
of this new channel in this harness remains pending; repository checks are not proof.

Actual child terminal/backing identity verified before builder restart. Same six
scratch filesystems and7193file authenticated Systemd source restored under new
shell-builder-restore-3 receipt. New bootbbd88a3c-bb6b-48ae-9d31-6beb22453b4c.
Native3 context complete-with-incomplete-evidence; never boot stale overlays/replay
restore3. The raw failed evidence is preserved. Continue minimal application work;
B02/G2 remain incomplete, finish all B02 then stop as requested.

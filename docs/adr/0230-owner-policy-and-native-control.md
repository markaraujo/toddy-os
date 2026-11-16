# ADR-0230: Fixed owner authentication and structured native control

Date: 2026-11-16. Status: implementation; native qualification pending.

B04 retained native IPC/package/configuration/Stop proofs but lacked a qualified
installed owner policy surface and structured systemd/NetworkManager operations.
Keep the same executor and independent durable policy store.

A fixed root-owned Python isolated-mode helper is the sole new Polkit grant
surface. Its exact executable path has a dedicated action, with active-session
`auth_admin` and no cached authorization. The helper takes the caller UID only
from pkexec, fixes the state directory and resolves session grants using logind
Display/User/Active/Remote properties. It cannot take a target UID, state path,
session, script or callback from imported profiles or model output. Standing
full administration remains explicit, expiring and independently revocable.
Root's existing policy CLI remains a deliberate manual rescue path.

Source: [Polkit pkexec reference](https://www.freedesktop.org/software/polkit/docs/latest/pkexec.1.html),
reviewed 2026-11-16 against the locked Polkit 127 integration. pkexec supplies
PKEXEC_UID and matches actions by executable path. Python isolated mode follows
the installed Python 3.14 contract; no user import path is retained. Actual
PAM/Polkit dispatch remains required before claiming native owner acceptance.

Structured service start/stop/restart/reload and global networking on/off use
fixed absolute native executables, bounded arguments and explicit postcondition
queries. No flag, unit path, arbitrary environment or repository override comes
from a model. Every dispatch still passes the independent current grant and
serialized durable operation record. Arbitrary root commands remain available
only under explicit unrestricted-root acknowledgment; this is not a restricted
substitute for the product's full administration requirement.

Host tests cover malformed identities, session mismatch, argument injection,
Stop before dispatch and successful process exit with failed postconditions.
They do not prove a booted daemon, PAM, cgroup cleanup or physical networking.
Qualification will use one new disposable overlay of the accepted B02 target,
with no physical disks, no imported secrets and unchanged cold backing disks.

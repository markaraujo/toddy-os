# ADR0155: Qualify Polkit's standard helper profile separately

Status: selected native candidate, installation pending, 2026-11-09.

The optional socket-activated Polkit helper profile remains unqualified. Actual
correct-password tests failed127 with No session for cookie. Two corrective
attempts did not resolve it; preserve that input/cause budget and failed native
contexts. DConf was independently completed before returning to this branch.

Exact frozen source distinguishes an authentication session from a logind
session: polkitbackendinteractiveauthority.c binds the cookie to the initiating
agent/subject UID. The socket helper obtains SO_PEERCRED UID and passes it with a
pidfd; the embedded pkexec agent is in a SUID process. This suggests a UID-binding
mismatch for that transport; it is a source-backed diagnosis, not a measured
credential trace or permission to waive the failed test.

The same source explicitly supports a standard SUID helper fallback when the
optional socket is absent. The upstream install script requests both exact
root:root4755 binaries in ADR0153; installing units does not enable the optional
helper socket. Qualify this separate supported default profile in a new native
child, leaving the socket unstarted and unadvertised. No global security setting,
source patch, passwordless policy or host permission change is introduced.

Require actual correct/wrong-password and unsolicited-cookie refusal, deny and
no-agent challenge, child NNP refusal, Stop with no target effect/helper cleanup,
recovery, daemon reconnect and action replay refusal after policy revocation.
Record generated credentials only in transient process/terminal memory. Preserve
exact fixture files and old socket failures; never mark them passed because the
separate default profile works. Owned installation still requires an exact
path/hash privilege policy and its own full-root/postcondition transaction.

# ADR-0174: Owned GeoClue backend and scoped native service policy

Status: native package and bounded service checks accepted; GNOME UI pending.

Use frozen GeoClue2.8.2, SHA256
`d4d65933b704d4c8d4ca9747dc511b883e35099abe534c8560f2aab3017e4cd4`,
from the official versioned archive and BLFS13.1-systemd basicnet/geoclue2.html.
This supplies the required GNOME Shell Geoclue2.0 import without a library-only
substitute. Keep backend, library, GI/Vala, WiFi, IP, static and compass support.
Optional ModemManager/NMEA hardware paths and demo agent are omitted through
supported Meson options. GNOME's own agent is still required for desktop integration.
No new hardware/provider availability is inferred from compilation.

The isolated build retained44compiled ELFs and32staged regular files. Upstream
registered no automated tests in this profile: the empty registry is preserved,
never counted as a passing suite. Own actual C GObject/D-Bus skeleton and typed
variant/refusal/recovery checks, daemon version and invalid-option checks passed.
Install the reviewed production stage with complete GPL/LGPL source notices,
conffile ownership, locked UID/GID30 and the upstream hardened nonroot service.
Only demo desktop/executable files are removed; commented public provider-key
examples are replaced by placeholders, without logging values or importing the
book's Google-key override. WiFi data submission remains disabled by default.
Installation grants no owner location consent.

Initial install recipe0/post1 exposed an own Python GI assumption: generated
interface setters are not methods on the Python skeleton object. Correct the
consumer to use actual writable GObject properties. Read-only verify2 passed
recipe/post0/0 with ZERO root changes and unchanged70owned entries/archive/account.
Never reinstall or recreate the account to fix a postcheck.

Run the actual installed daemon as UID30 with no-new-privileges and actual kernel
peer UID101 on a private system bus using the installed bus policy. Namespace-only
public passwd/group/config, static coordinates and synthetic agent fixtures expose
no real credentials or external routes. The first fixture failed before daemon
startup because target setpriv was absent; use builder setpriv before chroot.
The next fixture incorrectly expected per-app AuthorizeApp on a native peer.
Frozen src/gclue-service-client.c handle_post_agent_check_auth explicitly treats
peers without Flatpak-derived xdg_id as system apps. src/gclue-client-info.c derives
that identity from the real peer cgroup. Do not forge sandbox identity or change
upstream authorization to satisfy an incorrect fixture. Preserve both failures.

Services3 passed configuration denial, missing DesktopId refusal, distinct-peer
property refusal, service-name ownership refusal, global agent accuracy revocation
and recovery, explicit Stop and two distinct bus GUID cycles. Assert no per-app
AuthorizeApp was invoked for this native peer. All child processes exited, the
successful private profile was removed, and full-root recipe/post0/0 recorded ZERO
installed-root changes. Failed profiles1/2 and their logs remain for diagnosis.

This evidence does not qualify sandbox per-app consent, GNOME graphical prompts,
owner position, sensors, public location providers or actual network scanning.
Native graphical acceptance remains mandatory for B02. Continue with the selected
NetworkManager/NMA/GDM/GNOME Shell chain, preserving accepted package evidence.
[Build, package, failures and native service proof](../evidence/B02-geoclue-install.json).

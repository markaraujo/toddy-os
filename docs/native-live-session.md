# Fresh GNOME live session and fixed installer authorization

This source implements a separately attributed live-only transformation after a
real generation2 NativeFinalizer result. It is not a booted/live-login/Polkit
acceptance receipt. It does not change the accepted foundation images or copy a
builder/owner home. H10's root-console rescue profile remains historical recovery
material and is not the default Phase2 GDM owner profile.

## Native source contract

The selected frozen upstreams remain GDM50.2, GSettings Desktop Schemas50.1,
Dconf0.49.0, Linux-PAM1.7.2 and Polkit127, with their exact source hashes in sources.lock.json.
GDM50.2's original `data/pam-lfs/gdm-autologin.pam` requires UID>=1000 and includes
shared system-account/system-session. The live transform retains that selected
owned stack and prefixes only a toddy-live user check and fixed root live-boot
PAM guard; it does not edit global system-auth/system-account/system-session.
Polkit127 `src/programs/pkexec.c` supplies the authoritative program detail for
the exact annotated root entry. The new rule matches that program and one action,
never generic pkexec or a caller-provided command. Linux-PAM1.7.2
modules/pam_succeed_if/pam_succeed_if.c implements the exact user equality
condition; modules/pam_exec/pam_exec.c provides PAM_USER/PAM_SERVICE/PAM_TYPE
without expose_authtok. These primary source checks do not replace actual native
PAM qualification. Schema key names/types for live
lock/idle defaults are checked against actual selected frozen schema XML before
native Dconf update. No framework, frozen version or global display permission is
changed; no xhost/X11 weakening or owner session/keyring environment passthrough.

## Fixed source preparation API

`live_profile.stage(assembly, manifest, policy, media_id, LinuxDisk())` requires
`/sources/stage/toddy-live-image-2` and its inode-pinned live-root-2. It reads the
coordinator's finalized.json, verifies exact manifest/policy/source pins, actual
nine finalizer report files/hashes/results, the fixed reviewed generated map and
current independently audited whole image. A boolean callback/marker cannot
replace these inputs. Existing live intent/output or an uncertain generation is
preserved/refused before another transform.

`media_identity(payload_manifest_sha256, policy_sha256)` hashes the canonical
version/kind/input hash record plus actual live_profile.py source hash. It is
chosen before staging/compression. `/usr/share/toddy/live-image.json` has exact
fields version1, image_class=phase2-live-installer, live_uid1000,
live_user=toddy-live, media_id, producer_sha256, unit_sha256 and
profile_source_sha256. Media composition reuses that ID for the unchanged H10
initramfs marker; compressed root SHA is measured separately. Final image/rootfs
hashes are not inputs to their own class identity.

The fixed transform adds only fresh locked toddy-live UID/GID1000, empty0700
user-owned home, rootlocked baseline with unchanged empty wheel97, selected GDM
autologin config/PAM guard, a live-only GDM condition dropin, root producer unit,
fixed isolated Python wrapper, exact installer Polkit rule and live Dconf defaults.
The user is not added to wheel/disk or an assistant grant. Live lock/idle are
disabled for the passwordless ephemeral desktop; no installed-user preference
is reset. GDM's upstream once-per-boot autologin means a deliberate live logout
may require rebooting the ephemeral media; there is no password/root-console
fallback. Actual native usability must qualify this before a release claim.

Dconf update is the only native post-transform generator. Complete before/after
metadata/hash delta is checked against the fixed declared file/ancestor/output
set. Unknown changes are a failure, never a copied dirty root. The caller then
runs unchanged H10 ACL-sidecar and complete compression snapshot/journal logic;
this module does not duplicate that sidecar. The live-profile intent/receipt and
full live snapshot stay outside the image and always report no native boot/login
acceptance. The inherited foundation root getty autologin files and baked runtime
authority markers are explicitly refused.

## Authority checked again at the actual root GUI entry

The live-only rule permits only `io.github.markaraujo.Toddy.Install` for program
`/usr/libexec/toddy-installer-auth`, local active subject named toddy-live. It does
not authorize acquisition, executor operations or another executable. The root
entry then independently requires actual PKEXEC_UID1000 and validates:

- root-protected ID=toddy and actual toddy.live kernel token;
- root-owned imageclass, exact producer source/unit hashes and matching original
  H10 runtime media-ID marker; class/marker alone are insufficient;
- current kernel boot ID;
- active running exact root systemd producer, root kernel UID/cgroup/MainPID and
  current InvocationID;
- actual logind Display session: UID1000/toddy-live, local, active, unlocked,
  Wayland user class and GDM autologin service;
- exact private0700 root runtime directory and0644 root session attestation
  binding those independently queried facts, including current session ID.

The root systemd producer queries only kernel/logind/systemd state every2seconds,
publishes a new atomic session attestation only for those actual facts and removes
its own attestation when the session is absent/locked or the service stops. It
has a read-only system, private tmp/devices, no capabilities/new privileges,
AF_UNIX only, no keys, network/model/provider operation or authentication polling.
The root GUI guard independently rereads current facts, so logout/relogin,
producer restart, lock or another boot cannot inherit a stale grant during the
sampling interval. Source report/marker presence never makes a missing native
composition or native Qt/Calamares display qualification ready.

Existing exact disk target/plan review, confirmation, password FD, Stop boundary,
backend custody, root GUI clean environment/Wayland peer and production composition
checks remain required after this guard. Root-only show-only native launch
qualification remains separate from end-user production availability.

## Installed projection and native proof still required

The installer package/source helper, live user/profile/imageclass/rule/unit/wrapper
and runtime markers must be absent from the installed offline projection. That
projection is freshly reconstructed from its separate signed archive closure,
never copied from this live root. Existing acquisition/executor owner policies
and installed fresh-owner PAM are unchanged. Installed hygiene must explicitly
confirm those exclusions, no inherited password/keyring/provider/grant and fresh
machine identity.

The coordinator still must run actual live GDM autologin/PAM/Wayland, exact
live owner authorization, locked/background/other-UID/nonlive/stale-session
refusals, no generic root action, genuine root Qt/Calamares GUI/cancellation,
root producer lifetime, native Dconf and full image attribution/boot/install proof.
Source tests inject session facts/metadata only; they create no native service,
Polkit authorization, image, VM, account or password and claim no acceptance.

# Phase 2 — Package ownership and lifecycle

Selected design, 2026-11-07; no packages are built by this document.
[packages.json](../config/phase2/packages.json) assigns exclusive paths and names.
Capability dependency groups are symbolic until B01 locks actual native packages,
versions and licenses. Reuse existing staging/ownership and signed APT machinery.
Never translate these names into Ubuntu/Debian repository dependencies.

| Package | Responsibility | Offline base |
| --- | --- | --- |
| toddy-branding | Shared wallpapers, catalog/defaults, identity exports | Yes |
| toddy-assistant | Lightweight setup and native UI/CLI launcher; backend discovery | Yes, opens with backend absent |
| toddy-agent | Per-user broker, Pi worker and shipped profile preset | No; acquire during explicit later setup |
| toddy-executor | Independent system-bus service and authenticated owner policy | No; acquire with reviewed agent closure |
| toddy-installer | Live-only installer adapters and scenes | Live medium only; remove from installed image |
| toddy-voice | Optional speech adapter; engines/voices separately licensed | No |
| toddy-integrations | B10 tools/skills adapter and containment policy | No |

Upstream GNOME/browser/engine/model packages retain their own file ownership.
A package does not own another package's directory simply because it shares a
parent. No duplicate payload or overwrite flags. Placeholder module/icon paths
must be resolved against the locked target before packaging. The installed setup
UI uses the normal native package authorization flow to acquire the absent agent;
it cannot depend on the absent agent/executor to install that same executor.
After acquisition, probe actual service/version capabilities before enabling tasks.

## Upgrade, removal and recovery

Stop new dispatch before a service upgrade. Wait for safe operation boundaries;
never kill a package write merely to satisfy a UI timer. Keep operation journals
until postconditions are reconciled. Validate incoming configuration and preserve
a prior valid revision before atomic migration. Refuse an incompatible store
version visibly and leave recovery accessible; do not downgrade a migrated database
without a verified compatible backup. Unchanged inputs reuse accepted evidence.

Native package metadata declares conffiles and exact dependencies. Preserve user
changes to /etc policy and XDG profile files. Shipped defaults are immutable inputs,
not files rewritten over the user's persona at login. Package removal stops service
activation and revokes its capabilities; it does not recursively delete user
profiles, exports or memories. Explicit data deletion is separate and reviewed.
Root policy/state remain root-owned with restrictive permissions and no secret logs.

Removing the agent leaves GNOME and the setup UI usable. Removing voice/plugins
leaves text/base functionality available. Removing branding must leave readable
upstream defaults and report missing wallpaper references without resetting
unrelated settings. Preserve a usable text/recovery route across failed updates.
No model deletion is implied by disabling a profile.

Installed-image closure excludes installer/live accounts, live autologin, build
credentials, signing keys and source caches. Regenerate machine identity and verify
persistent ownership. Verify offline base installation and later agent acquisition
as separate S18/S19/S26 paths; a feature-complete G2 candidate must additionally
prove the scoped B03-B10 functions after acquisition. Offline deferral does not
waive those release-development acceptance criteria.

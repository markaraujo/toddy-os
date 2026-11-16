# Native B11 desktop background upgrade

This is source preparation, not an installed or visual acceptance receipt. The
coordinator remains the only guest writer. Accepted B02 evidence, original stage,
archive and package record remain unchanged. No build, VM write or settings change
was performed to prepare this slice.

The separate `toddy-desktop-defaults` version `0.2.0-1+toddy2` uses the existing
`branding_stage.render_desktop_defaults()` renderer. Only `picture-uri`,
`picture-uri-dark` and `picture-options` settings change. Light/dark approved
wallpapers are required at their existing `toddy-branding` paths and verified by
source SHA and native package ownership. Other dconf defaults, Terminal settings,
favorites, fonts and explicit user database values remain intact. No locks, home
files, schema overrides, artwork copies, exports or global styling are added.

## One native transaction

Deliver committed scripts through the existing verified metadata route. The
actual `toddy-branding` native package must already be installed. The driver
requires the original defaults archive and record in `/var/cache/toddy/packages`
and `/var/log/toddy/packages`; their hashes must match the committed B02 manifest.
Every current owned baseline payload file must still match its original hash,
mode and ownership, including both conffiles and the generated database. An
administrator edit or unknown generated-cache change blocks promotion for
explicit diagnosis; the recipe never silently resets that state.

Run in the guarded builder, after reconciling all running/failed writers:

```sh
umask 022
python3 /opt/toddy-build/scripts/build/run_step.py \
  b11-desktop-background-upgrade-1 \
  /opt/toddy-build/scripts/build/phase2/desktop-background-install.sh \
  /opt/toddy-build/scripts/build/phase2/desktop-background-check.sh --user root
```

`run_step` holds the existing global build lock and retains full-root mutation
manifest, command/postcheck exits, source/recipe pins and durable running/failed/
success markers. A failed marker is not permission to repeat an uncertain write.
The source driver also binds the running transaction, recipe hashes and parent
PID. It refuses existing new stages, archives, records and receipts. No nested
build lock or new isolation framework is introduced.

Native `dpkg-deb` extracts the exact old archive to the NEW
`/mnt/lfs/sources/stage/phase2-toddy-desktop-defaults-2` stage. Extraction is checked
against the frozen original payload, including absence of extra files. The three
keys are rendered there, the native `dconf compile` builds its owned database,
and the existing stage packager performs dependency, ownership and controlled
native dpkg promotion. The package adds a source manifest and a README correction;
legal notices retain the existing provenance rules. Its new dependency is
`toddy-branding (= 0.2.0-1+toddy1)`. No current-root copying is used.

The independent postcheck verifies actual archive, installed payload hash/mode/
UID/GID and dpkg ownership, both historical custody inputs, `dpkg --audit` and
`apt-get check`. A fixed UID101/NNP consumer in a private dev/proc mount namespace
reads the installed dconf backend through two fresh session buses. It checks exact
light/dark URI/zoom, unrelated defaults, unlocked owner override persistence and
reset. Only its disposable private home is created/removed. This is native default
and user-preference behavior, not graphical rendering.

Retain `/var/log/toddy/build/b11-desktop-background-upgrade-1.*`,
`/var/log/toddy/phase2/desktop-background-{upgrade,check}-1.json`, both native
package versions and stages. Review the full-root changed paths before image
composition. The exact original-package allowlist addition follows all existing
`image_projection` recipe-set, packager and owned source-manifest checks; it does
not admit arbitrary empty-source packages or change image closure selection.

## Recovery and rollback

Prefer exercising this in a fresh disposable overlay. If interrupted, inspect
`dpkg-query`, `dpkg --audit`, the transaction log/manifest, actual conffiles and
both package records before any next write. Do not rerun the original B02 recipe,
reuse this step ID, delete a running marker or copy database files manually.

The rollback source is the retained original
`toddy-desktop-defaults_0.2.0-1+toddy1_all.deb` (SHA-256
`24b35fcc03fe9ad338109181552e55b07fb250a99942157f8945facecf125907`), also retained
in the new `-baseline.deb` staging input. For a candidate rollback, first verify
that the current installed upgrade payload still matches its record. Use a NEW,
reviewed `run_step` root transaction with the standard package backend to install
that exact original archive; keep `--force-confold --force-confdef` policy and
stop for any edited conffile. Its independent check must require the original
version, original payload hashes/modes/owners, original empty URI/`none` defaults,
`dpkg --audit`, dependency checks and unchanged explicit user preferences. Retain
the failed upgrade and rollback receipts separately. No rollback was executed or
qualified by this source slice. A modified user's preferences are never deleted
as part of reverting system defaults.

## Validation still due

Run the native transaction once, inspect its whole-root manifest, then use a fresh
actual GNOME owner session to inspect effective light/dark URI/hash, desktop and
Toddy launch/focus screenshots, 32/48/64 icon readability and actual display
scales. Existing users with explicit backgrounds should retain their choices.
Login/installer scenes and removal fallback need their own actual native visual
proof. Repository assets or these source tests alone do not complete B11.

Focused source checks:

```sh
python3 -m unittest discover -s tests -p test_desktop_background_upgrade.py -v
python3 -m unittest discover -s tests -p test_branding_stage.py -v
python3 -m unittest discover -s tests -p test_image_projection.py -v
```

The small archive test builds a disposable fixture `.deb`; it never installs it,
compiles a native dconf database or produces an acceptance receipt.

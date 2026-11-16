# Exact native PipeWire base recovery

The actual `b09-pipewire-tools-1` package transaction completed its recipe but
failed its postcheck: five GNOME/audio packages pin PipeWire 1.6.8-1+toddy1
exactly, so installing revision2 broke APT consistency. Preserve the failed step,
full-root manifest/log, revision2 native archive/record and successful compile2.
Do not run an APT solver, retarget those five packages or replay that upgrade.

The new guarded recovery source first requires the exact observed failed0/1
ledger hashes, installed660-entry revision2 payload, unchanged649-entry baseline,
known five native reverse dependency records/versions/Depends and the exact
observed APT100 failure. It verifies the original retained archive/record and
refuses scripts, triggers, conffiles or unrelated failures. Nothing is recompiled.

From `/opt/toddy-build`, the sole guest writer runs:

```sh
python3 scripts/build/run_step.py b09-pipewire-base-restore-1 \
  scripts/build/phase2/pipewire_base_restore_install.sh \
  scripts/build/phase2/pipewire_base_restore_check.sh --user root
```

The accepted native PackageBackend installs only the exact retained original
PipeWire1 archive, under this NEW full-root transaction. This explicitly restores
the selected old revision; it does not invoke forced APT repair. Postcheck
independently requires old native version/SDK, all649 old bytes/modes/owners/links,
all11 revision2 additions absent, unchanged reverse dependency records, empty
Dpkg audit and APT0. An existing/uncertain recovery receipt blocks replay.

The private own receipt is
`/var/log/toddy/phase2/pipewire-base-restore-1.json`, final state
`native-pipewire-base-restored`, with `old_payload_unchanged: true`, sorted
`added_paths_absent`, integer `apt_check_exit: 0`, baseline archive/record SHA,
source inputs and `failed_upgrade` bound to the exact failed step/archive/record/
manifest. The separate full-root success receipt must also contain recipe0 and
postcheck0. Source fixtures are not recovery success. Actual native proof remains
pending until the coordinator executes and inspects those real postconditions.

Only after this succeeds may a separate `pipewire-audio-tools` package consume
the existing successful frozen compile2/stage and own pw-cat/aliases independently.
The base package, exact GNOME dependency pins and frozen compiler/voice/audit
inputs remain unchanged. Restoring the base does not qualify audio transport or
new tools; those require their own actual package/process checks.

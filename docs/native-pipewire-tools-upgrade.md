# Frozen PipeWire pw-cat native addition

The accepted PipeWire 1.6.8 base recipe disabled automatic features without
explicitly enabling pw-cat/libsndfile, so its installed package has no
`/usr/bin/pw-cat`. This prevents real voice capture/playback process validation.
The narrow upgrade is `pipewire_1.6.8-1+toddy2_amd64.deb`; it does not upgrade
upstream PipeWire, replace its libraries/configuration or qualify audio by itself.

The fixed native baseline archive SHA is
`6fcccccb584101ebf0899dcabbc64ff8551f8cc4e58356bc8878febc6a17c56a`, with retained
record SHA `ebdad900696ab299bcc7be52dcbde490c0a2a6d5afb3b659acb89cb6c2a77303`.
The existing frozen PipeWire 1.6.8 source archive SHA is
`efbaedf80450e5b08bb3196a4ca7ea17850d4a71ec1a8ae321e8937a7c95779e` from
`BLFS13.1-systemd multimedia/pipewire.html`. The full root source legal collection
is already in the old package and is preserved byte-for-byte. No source/license
lock or existing voice/audit input is modified by this helper.

The coordinator runs only the following source commands inside the designated
builder after reconciling its current writer, target identity, mounts and space:

```sh
python3 /opt/toddy-build/scripts/build/phase2/pipewire_tools_native.py prepare
python3 /opt/toddy-build/scripts/build/phase2/job.py pipewire-tools-build-1 \
  /mnt/lfs/sources/phase2/inputs/pipewire-tools-1 \
  /mnt/lfs/sources/phase2/work/pipewire-tools-1 \
  bash /src/toddy-pw-cat-build.sh
python3 /opt/toddy-build/scripts/build/phase2/pipewire_tools_native.py qualify
python3 /opt/toddy-build/scripts/build/run_step.py b09-pipewire-tools-1 \
  scripts/build/phase2/pipewire_tools_install.sh \
  scripts/build/phase2/pipewire_tools_check.sh --user root
```

The final run_step command is executed from `/opt/toddy-build`. Preparation and
all generations are one-shot: keep partial source/work/stage/prepared/job/native
transaction records and inspect actual postconditions after interruption. Never
reuse a failed namespace, run install directly or manufacture a compiler exit.
The compiler job must have its exact isolated harness command and actual exit 0
before promotion. Its existing private PID/network/mount namespace runs UID101
against read-only source/native SDK and retains configure/compile/install/help
logs. The harness retains the global native build lock while compiling.

Preparation extracts the verified frozen source into a new root-owned read-only
input, then records one source modification: a unique `toddy-pw-cat` install tag
on the upstream pw-cat executable. The upstream six C files, options and exact
nine alias names are unchanged. Meson uses `-Dpw-cat=enabled -Dsndfile=enabled
-Dpw-cat-ffmpeg=disabled` with automatic features disabled and no dependency
fallback downloads. Ninja builds only `src/tools/pw-cat` and necessary private
link prerequisites. Meson installs only that tagged tool into the private stage,
including native build-RPATH removal; no rebuilt library/configuration enters
this new stage. The frozen relative aliases point to `pw-cat`. Actual native
`--help` and compiled/linked 1.6.8 version consumers are separate from capture,
playback, routing or physical audio acceptance.

Before installation, the root helper checks native installed provider versions,
archives/records and every direct ELF owner/hash. The new tool must be x86-64 ELF
without RPATH/RUNPATH, linked to declared native PipeWire/libsndfile/libc providers;
unknown owners fail closed. The upgraded dependency declaration retains the old
exact Depends string and adds libsndfile 1.2.2-1+toddy1 and the frozen GCC runtime
16.2.0-1+toddy1. The old package has no conffiles; unexpected conffiles or control
scripts/triggers refuse the transaction rather than dropping them.

The promotion extracts the **verified old archive** with native dpkg-deb, checks
all old payload entries including modes/ownership/symlinks and full file SHA, then
adds only pw-cat, the nine upstream aliases and
`/usr/share/doc/pipewire/pw-cat-upgrade-source.json`. It never copies a dirty
installed root, rewrites old copyright/notices or replaces an existing tool.
The 16 GiB target reserve remains unchanged, with measured expanded source/old
archive/tool-copy allowance and 512 MiB staging overhead. Standard stage_package
owns the actual native archive, dependency/conflict checks and dpkg transaction;
standard run_step retains full-root before/after attribution and postcheck.

The fixed owned ledger is:

- `/var/log/toddy/build/b09-pipewire-tools-1.success.json`, requiring actual
  `recipe_exit: 0` and `postcheck_exit: 0`.
- `/var/log/toddy/phase2/pipewire-tools-install-1.json`, final
  `state: native-tool-package-verified`, `old_payload_unchanged: true`, with
  `actual_audio_process_qualification: pending`. Its manifest binds old archive/
  record/source hashes, all new helper/recipe inputs, tag patch, native staged
  tool hashes and direct ELF providers.
- Standard retained old/new native archive/record paths in
  `/var/cache/toddy/packages` and `/var/log/toddy/packages`.

Postcheck independently verifies all old installed bytes/modes/links, every
installed new tool/alias, compiled/linked upstream version, new package closure,
empty dpkg audit and apt dependency consistency. Previous desktop/PipeWire
library evidence can be reused only for the actually unchanged old payload; it
says nothing about newly added recording/playback behavior. The failed voice
process namespace stays retained. Real subsequent process/device qualification
must use a new explicit namespace and consume this successful native ledger and
actual upgraded archive/payload, without editing frozen voice2 source or copying
an old success/catalog receipt. Source fixture tests do not count as a native
compile, package install or voice result.

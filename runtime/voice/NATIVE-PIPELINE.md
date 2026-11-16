# Optional native voice package pipeline

Source slice for B09; no native compile, engine inference, microphone, playback or
GNOME acceptance is claimed by this document. The coordinator is the sole guest
writer. Do not execute these entry points on the development host. They require
root, the fixed `/opt/toddy-build` source path and the existing QEMU/target identity
guard. No original B02/foundation recipe or accepted evidence is replaced.

The fixed input contract is [native-inputs.lock.json](native-inputs.lock.json).
Whisper.cpp 1.9.5 and eSpeak NG 1.52.0 build with the existing reviewed recipes,
RAM-bounded to at most eight compiler jobs. The driver binds their **actual current
bytes**, the native harness and its own SHA before preparation; a changed recipe
or source tree requires a reviewed new generation. eSpeak uses its file-only
fallback, without Sonic/PCAudio/MBROLA; no neural-voice quality claim follows.

The 147951465-byte full multilingual `ggml-base.bin` is a separate optional package.
Its provenance version is exact converted revision
`5359861c739e955e79d9a303bcbc70fb988958b1`, not an invented model release. Preserve
its locked original OpenAI MIT license and converted model card. No English-only
replacement, provider model, boot download or automatic license consent exists.
All four new packages have `offline_base:false`; none belongs in the offline
root/ISO closure. Model choice alone does not authorize network or recording.

## Inputs and one-shot execution

The host already holds verified inputs in
`.local/phase2/voice-native-inputs-1/`. This slice downloads no new bytes, compiles
nothing on the host and does not open audio devices. Transfer only the six exact
locked inputs into guest `/mnt/lfs/sources/`, retaining filenames and normal
root-only 0600 or root-readable 0644 modes. Do not acquire again when the cache
verifies. Verify every SHA/size using the lock before transfer/promotion. The
source/model acquisition helper remains [NATIVE-INPUTS.md](NATIVE-INPUTS.md); its
host reserve is 100 GiB + 512 MiB. This driver uses the existing target reserve of 16 GiB
plus 128 MiB and checks additional promotion/preparation headroom. Source copies,
compiler work and native archives consume additional **target** capacity; actual
post-build sizes must be recorded, not guessed from compressed source sizes.

The coordinator must first deliver the committed driver, consumer/process helpers,
current recipes/harness, frozen lock/metadata files, complete voice Python source,
and `tests/test_voice_process.py` plus the attributed `tests/fixtures/voice/human/`
files to `/opt/toddy-build`. Deliver the current ordinary `toddy-voice` native
package (including strict catalog/controller/child/session and regular reviewed
`pw-record`/`pw-play` wrappers) through its existing native package transaction
before the `process` step. Engine/model preparation does not substitute that
package. Existing native PipeWire 1.6.8/WirePlumber 0.5.15, GNU time, Python, CMake,
compiler and ELF inspection tools are prerequisites; a missing one blocks the job.
No second compiler or root writer may overlap these commands.

For a fresh named generation, for example `native2`, execute each command as its
own tracked coordinator operation and inspect its postconditions before the next:

```sh
bash /opt/toddy-build/scripts/build/phase2/voice-prepare.sh espeak-ng native2
python3 /opt/toddy-build/scripts/build/phase2/voice_native.py build espeak-ng native2
bash /opt/toddy-build/scripts/build/phase2/voice-qualify.sh espeak-ng native2
bash /opt/toddy-build/scripts/build/phase2/voice-install.sh espeak-ng native2
bash /opt/toddy-build/scripts/build/phase2/voice-check.sh espeak-ng native2

bash /opt/toddy-build/scripts/build/phase2/voice-prepare.sh whisper-cpp native2
python3 /opt/toddy-build/scripts/build/phase2/voice_native.py build whisper-cpp native2
bash /opt/toddy-build/scripts/build/phase2/voice-qualify.sh whisper-cpp native2
bash /opt/toddy-build/scripts/build/phase2/voice-install.sh whisper-cpp native2
bash /opt/toddy-build/scripts/build/phase2/voice-check.sh whisper-cpp native2

bash /opt/toddy-build/scripts/build/phase2/voice-prepare.sh toddy-voice-model-base native2
bash /opt/toddy-build/scripts/build/phase2/voice-qualify.sh toddy-voice-model-base native2
bash /opt/toddy-build/scripts/build/phase2/voice-install.sh toddy-voice-model-base native2
bash /opt/toddy-build/scripts/build/phase2/voice-check.sh toddy-voice-model-base native2

python3 /opt/toddy-build/scripts/build/phase2/voice_native.py process whisper-cpp native2
python3 /opt/toddy-build/scripts/build/phase2/voice_native.py catalog whisper-cpp native2
python3 /opt/toddy-build/scripts/build/phase2/voice_native.py catalog-package whisper-cpp native2
python3 /opt/toddy-build/scripts/build/phase2/voice_native.py extras whisper-cpp native2
```

The engine builds and consumers run through existing `isolated.sh`: UID/GID 101,
private PID/network/mount namespace, read-only declared `/src`, private writable
`/build` and `/stage`, no owner credentials, writable system root or audio device.
The optional model is data and has no build step. The ordinary global native
build lock serializes the compiler harness and native installation; a separate
voice-pipeline lease prevents simultaneous voice commands without recursively
locking the harness. Preparation refuses existing destinations. Every potentially
uncertain child/transaction gets a one-shot intent marker. Missing exit receipts,
a killed coordinator, a failed consumer or a partially installed package requires
inspection/checkpoint reconciliation; **never replay the command**. A fresh name
is not permission to duplicate an uncertain native installation. Existing packages
are refused by the engine/model installer until a reviewed update is designed.

Receipts and logs are `/var/log/toddy/phase2/voice-COMPONENT-GENERATION.*`;
input/work roots are `/mnt/lfs/sources/phase2/{inputs,work}/voice-COMPONENT-GENERATION`.
Require actual outer build exit 0, recipe/source/harness hashes, RAM budget,
original eSpeak CTest exit and nonempty WAV postconditions. Native qualification
inspects every staged ELF for x86-64 and disallows embedded RPATH/RUNPATH. It
resolves recursive DT_NEEDED providers from the **target** ldconfig/dpkg databases
and pins their observed versions; no host `ldd` or invented dependency list.
Native `stage_package.py` retains source provenance, per-file legal headers/named
notices, normalizes ownership and performs the serial real native dpkg transaction.
Installed checks hash/mode/owner/link-match the record/archive and run native dpkg
and APT consistency checks. Target re-execution uses the actual installed binary.
A successful unpack alone is insufficient.

## Native write audit and lock boundary

The first engine/model `install`, initial `catalog` file creation and
`catalog-package` transaction retain the existing `run_step.snapshot` full-root
build manifest convention (usr/etc/var/tools/lib64/boot; source/build scratch
remains excluded). These new write recipes have not earned optimized-install
qualification. Under the **same already-owned global build-lock FD**, the driver
records immutable intent, full before/after snapshots, sorted add/change/removal
diff, exact command/interpreter/helper/source-lock pins, actual command exit and
independent package/catalog postcondition exit. A terminal complete receipt is
written only after both exits are zero and all snapshot/diff evidence is durable.
This captures changes after they occur; it does not confine privileged writes.
Inspect the diff against the package record and declared generated resources;
final independent image audit and native acceptance remain separate requirements.

The phase prefix receives `.{install,catalog,catalog-package}-audit.` files ending
in `intent.json`, `before.json`, `after.json`, `manifest.json` and either
`complete.json` or `failed.json`. A matching global
`/var/log/toddy/build/voice-COMPONENT-GENERATION.PHASE-audit.running.json` remains
until a terminal audit is durable. An interrupted snapshot/write leaves its
intent/running/partial state for inspection and blocks the ordinary dispatcher and
isolated harness; no guessed-success receipt, automatic removal or replay exists.
All failed/partial/completed generations are one-shot. Successful package checks,
process qualification, catalog creation/adoption and extras publication input
must match the prior successful audit, its command/source pins, package-record
hash and complete evidence checksums. Missing or changed audit evidence fails
closed even when dpkg reports installed.

Invoke the documented voice CLI directly. **Do not wrap all voice phases in
`run_step`**: build, qualify, check and process consumers enter `isolated.sh`, which
must acquire the same global lock itself. The write audit reuses snapshot/atomic
write primitives inside the existing write-phase lease; it never recursively
launches the dispatcher or takes another lock FD. Read-only installed consumers
keep their own isolation/lock lifecycle. Long healthy full scans are monitored,
not restarted. No voice preparation has run at this source boundary: synchronize
the updated driver and common scripts/build helpers before the first prepare so
its frozen driver/recipe pins are current. Direct and Python isolated-mode script
execution resolve both reviewed helper directories from `__file__`, not cwd.

## Actual qualification and catalog boundary

`voice_consumer.py` uses the licensed, attributed human EN/PT WAVs, not synthetic
speech/stub transcripts. It runs the real frozen multilingual model and records
actual output, word error rate, per-command GNU-time wall latency and peak RSS.
The bounded basic regression requires WER ≤ 0.4 for each short fixture; failure is
preserved rather than replacing output with reference wording. The transcripts
are public fixture results, not personal prompts. The eSpeak consumer creates and
inspects nonzero PCM WAVs in both languages. No listener intelligibility or audio
hardware inference follows from file existence. Full attribution and conversion
hashes remain in the fixture manifest and native catalog package documentation.

After all three actual installed checks, `process` runs the native process-loss,
Stop/reap test suite with **zero skipped tests**, then actual `VoiceSession.speak`
with `play=False` and actual `ProcessRunner` Whisper inference on the fixed EN/PT
files. This root-controlled disposable qualification explicitly constructs the
fixed reviewed artifact/consent data. Production keeps its strict catalog/license
checks; there is no bypass flag or model-selected executable. Transport wrappers,
`pw-cat` and `pw-dump` get actual no-device `--help` process invocations. This
qualifies launch/transport bytes only; opening a session, enumerating devices,
PTT capture/release, playback, disconnection and actual native GTK EN/PT behavior
must still be measured separately in the coordinator's GNOME session.

`catalog` refuses absent/changed engine, model, package archive, process/module,
legal or transport receipts. Installed modules must match the actually tested
source bytes. All artifacts/notices are fixed root-owned regular files under the
existing native catalog contract; symlink transport commands are rejected. A
native UID101 import/preview verifies the generated catalog without touching
models/devices or activating audio. There is no `qualified:true` source template.
If catalog preview fails after generation, retain that path and failure and
reconcile it explicitly; do not delete/recreate an uncertain result automatically.

`catalog-package` produces a fourth optional `toddy-voice-native-catalog` all-arch
native package containing only that verified catalog, its real qualification
receipts, attribution metadata and original project legal documents. It depends
on the exact observed engine/model/voice/PipeWire/WirePlumber package versions.
It does not hash its own archive into its payload. Catalog ownership becomes
ordinary dpkg ownership; there are no install hooks, autostart, credentials, model
copies or recording consent. Changing native inputs requires explicit requalification
and a reviewed package update. B09 and release acceptance remain pending until
both native component and actual device/PTT/GNOME evidence pass.

## Explicit signed project APT extras route

`extras` emits `*.extras.json` with actual archive hashes/sizes, source provenance,
per-file notice paths, observed native dependency fields and payload byte counts.
It deliberately stays `available:false`, `native-qualified-awaiting-signed-release`.
These are publication inputs, not release signatures, license consent or a GUI
availability claim. Publish the optional package set **and its exact recursive
native dependency closure** through the existing authenticated project APT release
route only after its source/legal/whole-image audit; never add Ubuntu repositories,
use a remote shell script, treat a fixture signing key as a release key or enable
insecure repository options. The signer must bind actual repository origin,
trusted key fingerprint, signed Release/InRelease metadata, Packages/deb hashes,
architecture/version, all source/legal links, acquisition sizes and proof references.
No signing credential belongs in the runtime or these recipes.

After the installed owner explicitly reviews the available signed release record,
network size/space and the separate engine/model/voice terms, the ordinary native
administrative authorization path can acquire pinned versions from its already
configured `signed-by` project repository. For example, first inspect
`apt-cache policy`/`apt-get --simulate install` for the exact generated versions,
then explicitly use `apt-get --download-only --no-install-recommends install`
with those `name=version` pins and ordinary APT signature verification. Inspect
cached hashes against the signed record before the controlled install; no
`--allow-unauthenticated`, insecure-source override or unreviewed repository is
permitted. Installation of the small catalog package brings exact engine/model
prerequisites via ordinary native dependency resolution. Source qualification's
internal root transaction is not the installed owner's consent. A successful
native archive set alone does not authorize a UI network/terms prompt or automatic
acquisition at boot. Existing setup/acquisition and executor policy remain the
owner-facing authority; integration must supply their actual signed release record
before availability is advertised. Opening the voice panel never downloads.


## eSpeak native1 retained; installed RPATH correction uses native2

The coordinator measured native1 eSpeak build/upstream CTest exit0, then the
strict qualifier rejected `/stage/usr/bin/espeak-ng` DT_RUNPATH `/usr/lib` before
native package promotion. Keep that source/work/log/failure unchanged. Frozen
upstream1.52 source `src/CMakeLists.txt` and `src/libespeak-ng/CMakeLists.txt` set
`INSTALL_RPATH "${CMAKE_INSTALL_PREFIX}/lib"`; the new recipe adds only
`-DCMAKE_SKIP_INSTALL_RPATH=ON`. No ELF guard, driver, source/model/version/license
pin, test or generation artifact is changed to accept that old binary.

Use a NEW eSpeak generation native2 with the current recipe. Never reconfigure or
strip native1 in place. Inspect actual new build/test/stage outputs and require
zero installed RPATH/RUNPATH through the existing qualifier before promotion.
The source check here is not a successful rebuilt-native receipt.

Current `process`/`catalog` stages require all three checked components under the
same exact generation argument. The fresh-cohort example above therefore uses
native2 throughout. If Whisper or the model has already been prepared/built under
another generation, keep that actual job/result and coordinate a separately
reviewed exact adoption or a truly fresh cohort before process/catalog; do not
rewrite receipts, replay an uncertain operation or silently copy/rename accepted
artifacts to make their generation match. This correction does not add such an
adoption mechanism or rebuild an unchanged completed component automatically.


## Whisper native1 retained; actual frozen legal paths for native2

The coordinator measured native1 Whisper compilation100%, followed by staging
failure while the old recipe tried to copy nonexistent `ggml/LICENSE`. The frozen
archive has the real1078-byte root `LICENSE` (SHA256
`94f29bbed6a22c35b992c5c6ebf0e7c92f13b836b90f36f461c9cf2f0f1d010d`, MIT,
The ggml authors), plus independent per-file notices. It has no nested GGML license
file to retain. The recipe now stages the real root LICENSE, and qualification
checks its exact bytes plus the actual GGML CPU MIT leading notice from
`ggml/src/ggml-cpu/llamafile/sgemm.cpp` (Mozilla Foundation). The native speech
license overview includes those exact source notice bytes, and the existing
configured source-notices header policy independently retains the remaining
per-file/backend notices. Optional GPU/backend terms are not relabeled as one
CPU license. No invented GGML-LICENSE file or copied success receipt is produced.

The driver changed to correct this real legal contract. Its prepared source pins
therefore require a complete NEW native2 cohort for both engines and the model;
preserve all native1 failed/partial/build outputs. The coordinator chose the
small real Whisper rebuild after its measured roughly one-minute native compile,
rather than a new adoption mechanism. Do not change old driver/source pins in
place or import old success exits into the fresh cohort. Actual native2 build,
legal/stage/ELF/EN-PT inference/process and installed postconditions remain due.

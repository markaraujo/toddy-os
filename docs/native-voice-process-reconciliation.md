# Native2 voice process reconciliation

Source only; no model, audio, VM, native install or generated catalog was run or
accepted by this source slice. Existing native2 three-component build/install/
audit/check receipts and frozen driver/runtime/prepared inputs stay unchanged.
The failed original process2 marker/log/exit remains immutable, with its real
nonzero exit. It is never copied or reinterpreted as a success.

The coordinator observed complete native2 engine/model installs and file-only
checks, then actual process tests/file EN-PT inference/Stop reached the transport
check and failed because frozen PipeWire's earlier payload lacked pw-cat. The
separate PipeWire tool upgrade must actually pass before this new retry is
prepared; its source commit alone is not a qualification input.

## Required concrete inputs

The fixed source driver is SHA256
`5a1dc85c634e2c54edad42f94c7222ef5fba56331aadc5efbb849178474c6dee`.
`voice_process_reconcile.py` imports its actual `prepared`, `native_record`,
`verify_package_record`, `artifact`, `require_write_audit` and
`native_write_audit` validators without editing or monkeypatching them. Every
native2 component must still match actual prepared/source, qualification,
controlled install audit, checked receipt and installed archive/payload bytes.
Any shared pinned helper/lock/license drift blocks the bridge; it is not silently
accepted as compatible. The old failed process command/prepared hash/log/marker
must still match the retained actual original attempt.

The attempted `pipewire_1.6.8-1+toddy2` replaced library metadata but broke
reverse dependencies that require the exact original revision. Its actual
`b09-pipewire-tools-1.failed.json` recipe0/postcheck1 and rejected archive/record
must remain immutable. Never rename that failure to a successful installation.

Require TWO new actual controlled transactions: `b09-pipewire-base-restore-1`
and `b09-pipewire-audio-tools-1`, both full-root recipe/check exit0. The former
restores the exact original `pipewire_1.6.8-1+toddy1_amd64.{deb,json}` and all
original payload bytes, removes exactly the eleven additions derived from the
retained rejected archive, and passes APT consistency. Require its actual
`pipewire-base-restore-1.json` state `native-pipewire-base-restored`, original
archive/record pins, retained failed-upgrade pins, absence list and APT exit0.

The latter installs separate `pipewire-audio-tools_1.6.8-1+toddy1_amd64.{deb,json}`
from the already qualified native compile, with actual
`pipewire-audio-tools-install-1.json` state `native-audio-tools-package-verified`
and `old_library_payload_unchanged:true`. Independently verify the complete
original library payload remains unchanged and owned regular `/usr/bin/pw-cat`
matches the separate tools package plus actual mutation manifest. No model/
source download, engine rebuild, version switch or voice reinstall occurs here.
The tools record becomes an explicit seventh catalog qualification record and
an exact native catalog package dependency. The frozen runtime catalog schema
retains its four original native dependency fields; PipeWire points to actual
restored revision1, while existing process-control hashes pin the new tool bytes.

## One fresh actual read-only job

After actual base restoration and separate audio-tools install/check and any healthy writer finish, sync the two
new source files through the existing verified route. The same source producer
must remain unchanged through all phases; its SHA is part of every new receipt
and root write audit. In the guarded builder, run once per phase:

```sh
python3 /opt/toddy-build/scripts/build/phase2/voice_process_reconcile.py prepare
python3 /opt/toddy-build/scripts/build/phase2/voice_process_reconcile.py process
python3 /opt/toddy-build/scripts/build/phase2/voice_process_reconcile.py catalog
bash /opt/toddy-build/scripts/build/phase2/voice_reconcile_install.sh
python3 /opt/toddy-build/scripts/build/phase2/voice_process_reconcile.py check-catalog
```

Preparation records exact old installed/audit/source/failure pins and creates NEW
`/sources/phase2/work/voice-process-native2-r1`. The `process` phase dispatches the
existing frozen `/src/qualification/process-check.py` through EXISTING `job.py`
and qualified `isolated.sh`, using the immutable Whisper2 source mount and that
new work/job namespace. The real dispatcher records its own command, log and exit.
No success exit is fabricated, copied or renamed. The global build lock belongs
to that harness; the producer does not hold it recursively. The existing voice
pipeline lock excludes concurrent voice operations.

Successful qualification requires actual new exit0, exact native harness/command,
all runtime source hashes matching installed bytes, native process tests without
errors/failures/skips, nonempty EN/PT reference inference/WER, actual native
Whisper Stop, and actual fixed capture/playback/device-list/pw-cat help hashes.
Transport help is explicitly not an audio device, PTT/playback or GNOME proof.
The original failed process files remain unchanged throughout and their hashes
are retained in the new evidence.

## Controlled catalog/package writes

A NEW catalog producer consumes that explicit actual new job proof. It does not
redirect the frozen driver's reads or hide its failed process exit. The runtime
catalog schema, fixed reviewed wrappers, artifact/model/license hashes and
current native package records use the original validators. The normal native
UID101 catalog preview must pass with no always-listening or automatic download.

Both catalog creation and first optional catalog package promotion use the
existing full-root `native_write_audit` under the already-held global lock, with
actual commands/exits, producer/source/input pins and before/after manifests.
Existing destination/stage/markers refuse replay. The package version remains
first `toddy-voice-native-catalog_0.2.0-1+toddy1_all`, with exact dependencies on
all actual current component/transport/controller versions. It owns the real new
process proof, retry validation, catalog qualification and three actual engine/
model qualification documents; no engine/model executable or payload is copied
into the metadata package. The source recipe is `voice_reconcile_install.sh`.
There is no circular self-hash or claim that a package owns its later install
receipt. The independent checker revalidates actual controlled package audit,
installed bytes, catalog preview and dpkg/APT consistency.

Keep all `voice-process-native2-r1.*` receipts/logs, actual work outputs and both
root write audit sets. New failures are one-shot and require diagnosis and a
separately reviewed new namespace, never marker deletion. Native PTT/device/
playback/GNOME qualification, physical microphone/speaker, signed optional
acquisition and B09/G2 acceptance remain separate real gates. No source fixture
or artifact status flag grants production permission.

Focused source tests:

```sh
python3 -m unittest discover -s tests -p test_voice_process_reconcile.py -v
```

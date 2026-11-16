# Explicit optional native voice UI

The conversation's collapsed voice section provides English/Portuguese controls
without adding a new app framework. Nothing records, plays, downloads, acquires a
credential, starts a model, queries devices or submits a task on construction.
Missing optional voice package or unqualified artifacts leaves visible text
fallback. UI/model calls remain independent of the voice worker.

One VoiceController worker handles an explicit action. Metadata/notice review
happens off the GTK thread. No large weight hash or engine wait blocks GTK. The
owner reviews the exact installed engine/model notices, checks local-use consent,
refreshes actual PipeWire device nodes and explicitly selects microphone/speaker.
No device is selected automatically. Each action rechecks the reviewed catalog
pin and actual files; changed artifacts/notices require fresh review.

Push-to-talk uses a mouse hold or Space/Return. The held widget stays sensitive
until release, so disabling a busy button cannot swallow the release event.
Releasing during loading cancels before later capture. Recording/loading/local
transcription/playback/Stop states are visible. Focus loss, hiding/collapsing the voice controls, profile switch and
window close cancel voice; a worker never clears that cancellation. Every action
captures the profile generation; late old-profile callbacks/transcripts are
ignored. Text/audio scratch stays private and is removed by VoiceSession.

Transcripts are untrusted editable review text. A separate Insert action appends
the reviewed text to the existing message draft, rejects overflow instead of
truncating, clears remote per-request consent and never submits a task. Ordinary
Send still uses the same TaskClient/profile/provider/root policy as typed text.
Speech output is explicitly requested from a reviewed text field; copying a
visible reply is a separate action. Voice Stop cancels voice only, never an
unrelated broker operation. eSpeak is clearly identified as a synthetic voice.

## Fixed native artifact/license catalog

Production NativeVoiceCatalog accepts only the root-owned non-writable regular
file `/usr/share/toddy/voice/catalog.json`. Source packaging does not generate it.
The trusted native transaction must create it after actual engine/dependency/
model/license/device/process qualification. Missing/unqualified/malformed data
leaves voice unavailable; user JSON, a PATH match or a source marker is insufficient.

The exact top-level fields are voice_catalog_version (integer 1), status
(native-qualified), tts_engine (espeak-ng), native_dependencies, process_control
and artifacts. native_dependencies has exactly pipewire1.6.8, wireplumber0.5.15,
whisper-cpp1.9.5 and espeak-ng1.52.0; each entry has version and actual accepted
component_record_sha256. No source/baseline upgrade is selected.

process_control has launcher_sha256 (installed child.py), runner_sha256 (installed
process.py), pw_cat_sha256, pw_cat_bytes and actual evidence_sha256. Catalog checks
the installed control code and canonical pw-cat integrity. Native proof must
include the owner session's real capture/playback, selected-device disappearance
without fallback, Stop/close/focus loss, parent death and ordinary text fallback.
These source process controls do not claim arbitrary escaped-setsid containment.

artifacts maps exactly these six roles to the complete existing Artifact fields:
artifact_id, kind, path, size, sha256, source_url, version, license_id, license_path,
license_sha256, review (reviewed-local-use) and languages. IDs are unique. The
only accepted executable/model paths are:

| Role | Fixed regular path |
| --- | --- |
| capture | /usr/lib/toddy/voice/pw-record |
| playback | /usr/lib/toddy/voice/pw-play |
| device-list | /usr/bin/pw-dump |
| stt-engine | /usr/bin/whisper-cli |
| stt-model | /usr/share/toddy/voice/models/ggml-base.bin |
| tts-engine | /usr/bin/espeak-ng |

All parent components/actual artifacts are owned by root, not symlinks or writable
by other users. Notices must be actual hashed UTF-8 regular files below
/usr/share/doc. Model is the exact locked 147951465 byte multilingual base SHA256
60ed5bc3dd14eea856493d334349b405782ddcaf0028d4b5df4088345fba2efe. The model
is never loaded merely for metadata preview; action-time integrity is rechecked.
The ordinary Artifact symlink/hardlink/ownership/consent guard remains strict.

PipeWire's pw-record/pw-play may be symlinks to pw-cat; those symlinks are not
passed through the artifact guard. Two reviewed regular root wrappers explicitly
exec canonical /usr/bin/pw-cat in --record/--playback mode. They set per-stream
node.dont-fallback, node.dont-reconnect and node.dont-move. Device discovery reads
bounded pw-dump output and keeps actual Audio/Source and Audio/Sink object.serial
identities only. Every action rechecks the current graph and uses that serial,
not an auto/default route or a recycled graph node ID. Native qualification must
verify those properties on the frozen selected WirePlumber/PipeWire runtime;
source intent does not prove device policy. Current upstream reference describes
[explicit target serials](https://docs.pipewire.org/page_man_pw-cat_1.html) and
[no-fallback/reconnect properties](https://pipewire.pages.freedesktop.org/wireplumber/policies/linking.html);
those live docs are not an authorization to upgrade the frozen native versions.

## Packaging and validation handoff

The assistant source payload adds ui/voice.py and current EN/PT copy. It remains
usable when every optional voice module/catalog is absent. The optional voice
payload must add catalog.py, controller.py and child.py plus regular executable
wrappers at the two fixed paths above. No duplicate root namespace/shared helper,
native host executable, model/voice weight, qualification marker or receipt is
copied by the source stage. Native signed engine/model acquisition remains separate.

Host checks cover 12 existing synthetic speech-process/state cases, 3 actual
parent-loss/reap cases, profile/Stop/device-selection worker scope and actual GTK
EN/PT widgets with a deliberately synthetic non-audio controller. Real human WAVs
under tests/fixtures/voice/human are separately attributed/hashed and ready for
actual frozen Whisper EN/PT inference. No test transcript is a model result.
Native microphone/device/PTT/voice quality/latency/RAM, actual model inference,
UI screenshots and qualified catalog remain required before B09/S15 acceptance.
No host microphone, speaker, guest or provider was activated by this source work.

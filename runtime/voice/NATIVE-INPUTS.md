# Optional native speech inputs

This slice freezes the existing engine candidates without upgrading the foundation:
whisper.cpp 1.9.5 at d1be6fde11ac6e0407606b4e42fe72d34add8037 and eSpeak NG
1.52.0 at 4870adfa25b1a32b4361592f1be8a40337c58d6c. The selected fallback is the
built-in eSpeak `en-us` and `pt-br` formant voices. Piper remains deferred, with
no neural voice weights acquired. This does not change the voice adapter's
explicit artifact/license consent or authorize installed-user downloads.

`native-inputs.lock.json` binds full upstream commit archives, the **multilingual**
`ggml-base.bin` (147951465 bytes), original OpenAI MIT license, converted model MIT
card and the immutable LFS size/SHA256 pointer. The converted repository revision
is 5359861c739e955e79d9a303bcbc70fb988958b1; the source's pinned
[download script](https://github.com/ggml-org/whisper.cpp/blob/d1be6fde11ac6e0407606b4e42fe72d34add8037/models/download-ggml-model.sh)
selects that repository. Runtime licenses and model terms remain separate. The
converted [model card](https://huggingface.co/ggerganov/whisper.cpp/blob/5359861c739e955e79d9a303bcbc70fb988958b1/README.md)
declares MIT; the exact [original license](https://github.com/openai/whisper/blob/86098128c0b4f24f0e2aa2994de830614b474227/LICENSE)
is retained. Include those notices when distributing model bytes. Source/code/data
and dependency notices still require native package closure review; eSpeak COPYING
alone is not proof of every dictionary's provenance.

## Host acquisition and prepared input

Use an existing canonical private cache directory. `fetch` checks the host reserve
of **100 GiB + 512 MiB plus all missing downloads**, checks space during streaming,
uses HTTPS, exact size/SHA256, private partial files and atomic publication. An
existing file must verify; a partial/changed input is retained for inspection.
There is no implicit retry, engine launch, build, install, model inference or
audio-device access. Do not remove another writer's cache to gain space.

```sh
python3 scripts/build/phase2/voice_inputs.py fetch --cache /ABS/PRIVATE/CACHE
python3 scripts/build/phase2/voice_inputs.py verify --cache /ABS/PRIVATE/CACHE
python3 scripts/build/phase2/voice_inputs.py prepare --cache /ABS/PRIVATE/CACHE --kind espeak-source --output /ABS/NEW/ESPEAK-INPUT
python3 scripts/build/phase2/voice_inputs.py prepare --cache /ABS/PRIVATE/CACHE --kind whisper-source --output /ABS/NEW/WHISPER-INPUT
```

Preparation consumes at most 128 MiB expanded per archive in addition to the same
host reserve, refuses an existing destination and emits `prepared.json`. It
validates members and accepts only eSpeak's exact internal compatibility-header
symlink; no ownership/device/hardlink import. The returned source directory has
`toddy-build.sh`. No mount or privileged operation occurs. A failed preparation
remains for inspection, never silently replayed.

Two minimal hash-bound corrections are required for disconnected read-only builds:
eSpeak's [dependency logic](https://github.com/espeak-ng/espeak-ng/blob/4870adfa25b1a32b4361592f1be8a40337c58d6c/cmake/deps.cmake)
unconditionally fetches Sonic even when its feature is OFF; preparation removes
that fallback. Whisper's top-level CMake writes a JavaScript package metadata file
into the source; its output moves to the binary directory. Prepared receipts bind
original/corrected file hashes plus the exact recipe hash. Unknown originals fail.

## Single-writer native build and qualification handoff

The parent must import these reviewed inputs through the existing target guard,
source custody receipts and qualified UID 101 no-network/read-only-source staging
harness. Preserve target reserves and existing native CMake/Ninja/compiler/ABI;
do not run the build scripts directly on the development host. No new package
catalog availability or native signing authority is granted by input acquisition.

`voice-espeak-build.sh` disables Sonic, PCAudio, MBROLA and async output, keeps the
shipped phoneme/dictionary data, builds original CTest drivers and generates two
**file-only** WAVs. No audio output backend is linked. It does not claim audible
quality, actual Portuguese intelligibility or neural voices. Preserve original
upstream failures rather than changing expected results. `pw-play` from accepted
PipeWire performs optional explicit playback later.

`voice-whisper-build.sh` builds only the CPU CLI with bundled GGML, internal static
libraries and dynamically linked foundation libc/GCC runtime. Native CPU tuning,
AVX/AVX2/FMA/F16C/BMI2, OpenMP, CUDA, Vulkan, BLAS, curl, SDL, FFmpeg and server are
disabled. No vendor GPU runtime, new Python dependency or automatic model download.
Only the CLI and engine/GGML notices are staged. The recipe does not run upstream's
many-model matrix or pretend CLI help is inference; the full selected base model
requires the following focused real qualification.

1. Inspect target/boot identity and no conflicting operation; verify prepared and
   lock hashes. Run isolated compile/stage and preserve exit codes and logs.
2. Independently inspect staged ELF dependencies, ISA requirements, path/mode/owner
   inventory and source/license/data notices. Resolve only actual missing native
   dependencies with exact versions; use the existing verified-stage/native package
   transaction and signing path. Do not add voice to the offline base closure.
3. Bind installed engines, `pw-record`/`pw-play` from PipeWire 1.6.8 and separately
   verified model/notices into `Artifact` records. Exact installed package hashes
   and explicit local-use consent are required; source records are insufficient.
4. With independently reviewed short 16 kHz mono PCM16 **real English and Portuguese**
   WAV samples, use `whisper-cli -m /MODEL/ggml-base.bin -l en -f /PRIVATE/en.wav -otxt
   -of /PRIVATE/en-result` and then `-l pt` with the Portuguese sample. Save bounded
   private transcripts for human assessment, expected wording/tolerance, actual
   exit status, elapsed time and peak RAM. Never fabricate recordings or record a
   fixture transcript as recognition. Do not route a transcript into task authority.
5. Assess actual eSpeak EN/PT spoken output, real native device selection/PTT/Stop,
   text fallback, no always-listening and cancellation during model loading,
   inference and playback through the existing `VoiceSession`. Device permissions,
   installation lifecycle and optional voice acquisition UI remain independent.

This is actionable input/recipe preparation, not B09 or S15 acceptance. No guest
build, model inference, microphone/speaker activation or speech quality result has
been performed by this source slice.

## Reused native closure and health unit review

The committed B02 runtime projection already includes PipeWire
1.6.8-1+toddy1, ALSA 1.2.16.1-1+toddy1 and existing desktop audio policy. Their
package archives/source/legal receipt hashes are in
[the runtime manifest](../../docs/evidence/B02-desktop-runtime-manifest.json).
Inspect installed transport ownership/config before adding any new dependency;
do not reinstall the unchanged desktop audio stack merely to test voice.

`NativeHealth`'s selected `gdm.service` and `NetworkManager.service` are correct for
this native system. GDM 50.2-1+toddy1's real running unit is recorded in
[B02 native seat evidence](../../docs/evidence/B02-gdm-native-seat.json), and the
installed display-manager link in
[boot policy evidence](../../docs/evidence/B02-desktop-graphical-boot-policy.json).
NetworkManager 1.58.1-1+toddy1's unit/drop-in/enabling is recorded in
[network package evidence](../../docs/evidence/B02-desktop-network-install.json)
and actual recovery in
[native networking evidence](../../docs/evidence/B02-network-native-recovery.json).
No Ubuntu `gdm3.service` substitution is needed. This review reuses existing B02
facts; it does not prove a newly running automation timer or current guest state.

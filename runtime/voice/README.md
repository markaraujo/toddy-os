# Optional speech process adapters

This source slice provides explicit push-to-talk capture, local transcription,
on-demand synthesis and playback control. Nothing starts on import, capability
inspection or boot. No engine, model or voice is downloaded/installed by this
code. Text remains available when optional artifacts/devices are unavailable.
There is no always-listening mode, HTTP server or cloud fallback.

`candidates.json` records the exact official source/API/license bytes inspected
on 2026-11-16: whisper.cpp **1.9.5**, OHF Piper **1.8.0** and eSpeak NG **1.52.0**.
These are source/API candidates, not a change to the accepted foundation or a
native-qualified package lock. APIs were read at their recorded commits from
upstream [whisper CLI](https://github.com/ggml-org/whisper.cpp/tree/v1.9.5/examples/cli),
[Piper CLI source](https://github.com/OHF-Voice/piper1-gpl/blob/v1.8.0/src/piper/__main__.py)
and [eSpeak manual](https://github.com/espeak-ng/espeak-ng/blob/1.52.0/src/espeak-ng.1.ronn).
The existing design chooses multilingual Whisper base and Piper faber/PT-BR,
ljspeech/EN candidates. Their exact model/config bytes and distribution terms are
not yet locked, so no neural model/voice is enabled or redistributed. eSpeak is
an explicitly identified formant fallback candidate, with native data/dependency
qualification still pending; do not claim neural quality or actual intelligibility.

`Artifact` binds an absolute local engine/model/config path to exact size/hash,
source/version, separately hashed local license notice, reviewed-local-use status
and EN/PT languages. `Consent` binds explicit local use to the artifact **and**
license hashes. Missing consent, changed bytes/notices, symlinks/hardlinks,
unsafe permissions or unreviewed metadata fail before launching an engine.
Neither metadata nor consent authorizes network acquisition, redistribution,
provider spending, microphone capture or privileged tools. Native packaging must
supply trusted verified records, including installed engine/data dependencies;
a user-written metadata file is not a distribution trust root. Hashing is on
explicit activation and has not yet been benchmarked on real model bytes.

`VoiceSession` receives artifacts/consents by role: `capture`, `playback`,
`stt-engine`, `stt-model`, `tts-engine`, and Piper's `tts-model`/`tts-config`.
The capture/player executables are the selected package-owned `pw-record` and
`pw-play`; a PATH match alone is insufficient. `capabilities(language)` checks
availability without starting them. The TTS choice is explicit (`piper` or
`espeak-ng`) and reported to the caller; no silent engine/provider replacement.

Call `reset()` synchronously for a **new explicit user action** before scheduling
a worker. `push_to_talk(language, selected_device)` runs in a worker after the
microphone button is pressed. State callbacks report loading/recording/transcribing
and transcript-ready. `release_microphone()` sends an interrupt to end this one
capture and checks exit status plus a bounded mono 16 kHz PCM16 WAV before
transcription. A device ending before release is an error. Recording is bounded
to 30 seconds. `stop()` cancels capture/inference/playback and does not reset its
own cancellation; a queued old worker therefore cannot clear Stop and start
recording. The caller must marshal state callbacks onto its GUI main loop.
A state callback failure before capture prevents capture.

The returned transcript is bounded UTF-8 **untrusted text requiring review**.
It never submits a task, grants permission, invokes a tool or sends text/audio
externally. After user review, use the same ordinary broker/profile/policy path
as typed text. Speech is not a second authorization channel. `speak()` reads text
from a private file, verifies synthesized PCM16 WAV structure and optionally
plays through the explicitly selected device. `play=False` is engine-only scope.
Audio/transcript scratch lives in private temporary directories and is removed
when the operation ends; no transcript, response or raw stderr is logged here.
A transcript returned to the caller must follow existing per-profile retention.

`ProcessRunner` uses absolute verified executables, no shell, a small environment,
private umask, bounded discarded diagnostics and explicit deadlines. It terminates
the managed process group on cancellation/failure, escalating after a short bound.
This controls trusted speech engines; it is not an unknown-code sandbox and does
not prove containment of malicious children that escape process groups. Installed
service/cgroup lifecycle and actual device Stop remain native qualification work.
It never cancels an unrelated broker task or claims to undo an effect.

Focused checks:

```sh
python3 -m unittest discover -s tests -p 'test_voice.py' -v
```

Tests launch actual local child processes using **synthetic** WAV/STT/TTS fixture
executables: EN/PT protocol selection, PTT release, Piper/eSpeak invocation,
playback handoff, license/integrity refusal, cancellation of an unresponsive child,
deadline/output bounds and text fallback. They prove process/state handling, not
speech recognition, intelligibility, physical audio or an installed B09 component.
No microphone/speaker was activated and no engine/model was acquired.

Next native slice: freeze/source-build the required optional engine/dependency
closure without upgrading foundation ABI, obtain separately reviewed exact model
and voice artifacts only after explicit selection/terms consent, bind native
package files/notices, then run S15 with real short EN/PT recordings, intelligible
spoken replies, visible device/microphone/Stop states and measured latency/RAM.
The GTK microphone controls and shared text-task handoff remain integration work.
Only those observations can establish B09 acceptance; fixture output is insufficient.

## Trusted process lifecycle prerequisite

The fixed child launcher now arms Linux parent-death SIGKILL before engine exec,
then checks its actual parent to close setup loss. Losing the UI/controller cannot
leave the direct capture engine recording. ProcessRunner uses waitid(WNOWAIT)
instead of poll/wait while cleanup still owns a process group. Every group signal
precedes the one leader reap; no killpg occurs after that PID becomes reusable.
Unexpected outside reaping fails closed without signaling a reused group. Source
process tests prove actual parent loss, refused wrong-parent exec, cancellation
and cleanup while an exited unreaped leader's descendant holds an output pipe.

These controls apply to the selected trusted fixed native engines. They do not
claim cgroup containment of arbitrary/escaped setsid descendants or native audio
qualification. Root artifact/catalog qualification and native crash/device/Stop
proof remain prerequisites before UI activation. The optional voice package must
include child.py beside process.py; no caller-supplied launcher is accepted.

# ADR-0244: Package optional voice from actual native qualification

Date: 2026-11-16. Status: accepted source implementation; native proof pending.

B09 uses the already frozen Whisper.cpp 1.9.5 and eSpeak NG 1.52.0 fallback.
The exact full multilingual base model remains a separate optional artifact with
its immutable converted revision and original MIT/model-card notices. No engine,
model or qualified catalog is part of the offline desktop/ISO closure.

Use the existing guarded native UID101 isolation and source-built dpkg/APT
backend, not a new package framework. The source pipeline binds current recipes,
original source bytes, native ELF dependency providers, actual human EN/PT
inference and file-only TTS, installed payload/archive records, process-loss/Stop
proof and native no-device transport invocations. Preserve each intent/exit/log;
a missing postcondition never authorizes replay. Retain per-file eSpeak/GGML
conditions independently from an engine's summary license identifier.

A separate optional `toddy-voice-native-catalog` package owns the root artifact
catalog only after those actual receipts exist. It depends on exact observed
native engine/model/adapter/audio-stack versions, contains proof/attribution
metadata, and has no circular archive hash, autostart or acquisition consent.
The existing strict production catalog and owner notice/device review remain.
The disposable native qualifier may explicitly instantiate fixed reviewed
`VoiceSession` artifacts for real file-only tests before a production catalog
exists; no production bypass or fake qualification flag is introduced.

Emit actual native archive/source/legal/acquisition metadata as publication inputs,
keeping availability false until the ordinary signed project APT release and
closure audits pass. The installed owner must explicitly review network/space and
separate model/voice terms before ordinary authorized APT acquisition. Actual
GNOME device/PTT/release/Stop/playback/GTK evidence remains a separate required
B09/release gate. No source test or headless help result earns that acceptance.

See [native execution and recovery commands](../../runtime/voice/NATIVE-PIPELINE.md),
[frozen inputs](../../runtime/voice/native-inputs.lock.json) and
[B09](../../stories/B09.md). The source slice runs host fixture checks only;
actual guest evidence must be recorded by the single coordinator/guest writer.

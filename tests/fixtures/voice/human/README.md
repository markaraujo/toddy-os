# Real speech inference inputs

These are short licensed speech recordings from Wikimedia Commons, converted to
mono 16 kHz PCM16 WAV **without playback or microphone access**. They are real
speech input files, separate from ../engine.py's explicitly synthetic process
fixture. manifest.json binds original URL/author/page revision, source size,
SHA1/SHA256, selected license, conversion versions and exact derived WAV hashes.
The expected_text field is reference wording from the source recording's title/
description, not a model-produced transcript. No inference result is claimed.

- en.wav: *Audio Sample – The Quick Brown Fox Jumps Over The Lazy Dog*, Russell
  Sacobie / [RussmanJr](https://commons.wikimedia.org/wiki/User:RussmanJr), 2019.
  [Source and attribution](https://commons.wikimedia.org/w/index.php?title=File:Audio_Sample_-_The_Quick_Brown_Fox_Jumps_Over_The_Lazy_Dog.ogg&oldid=807167525).
  Original and this converted WAV: [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).
- pt-BR.wav: *Onde fica o banheiro?*, Ikescs, English Wiktionary, transferred to
  Commons by Kylu. [Source and attribution](https://commons.wikimedia.org/w/index.php?title=File:Onde_fica_o_banheiro.ogg&oldid=1125194889).
  Selected original license and this converted WAV:
  [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/).

Changes: decode Ogg, average channels to mono, resample with libsamplerate's
SINC_BEST_QUALITY and clamp/round to signed16 PCM. Attribution does not imply the
speakers endorse Toddy OS. Keep these notices, links, change description and
share-alike license when distributing the corresponding audio. The repository's
original-code MIT license does not replace these audio licenses.

Reproduce with the exact original files in a private cache, verify their recorded
hashes first, then use scripts/host/prepare_voice_test_audio.py with a fresh output
path. The conversion opens files only and records host library versions; it does
not establish a frozen native runtime or model compatibility. Original downloads
are not silently replaced/retried, and no corpus or large new dependency is needed.

Native qualification must use the actual qualified whisper.cpp 1.9.5 CLI and full
multilingual base model, pass --language en / pt respectively, and independently
save exact engine/model/input hashes, actual exit status, timing/peak RAM and
observed transcription agreement. Do not substitute expected_text for model
output. File inference does not prove microphone device selection, push-to-talk,
audible response intelligibility, physical hardware or B09/S15 acceptance.

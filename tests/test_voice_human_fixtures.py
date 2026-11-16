"""Actual licensed file input integrity/format only; no model or audio device."""
import hashlib
import json
from pathlib import Path
import struct
import unittest
import wave

ROOT=Path(__file__).resolve().parents[1]/'tests/fixtures/voice/human'


class HumanFixtureTests(unittest.TestCase):
    def test_exact_non_silent_real_source_wav_bytes_and_separate_terms(self):
        manifest=json.loads((ROOT/'manifest.json').read_text())
        self.assertFalse(manifest['model_inference_performed'])
        self.assertFalse(manifest['device_audio_performed'])
        self.assertEqual(set(manifest['samples']),{'en','pt-BR'})
        for language,row in manifest['samples'].items():
            with self.subTest(language=language):
                path=ROOT/(language+'.wav');data=path.read_bytes()
                self.assertEqual(len(data),row['wav']['bytes'])
                self.assertEqual(hashlib.sha256(data).hexdigest(),row['wav']['sha256'])
                self.assertTrue(row['source_page'].startswith('https://commons.wikimedia.org/'))
                self.assertTrue(row['license_url'].startswith('https://creativecommons.org/licenses/by-sa/'))
                with wave.open(str(path)) as audio:
                    self.assertEqual((audio.getnchannels(),audio.getframerate(),audio.getsampwidth()),(1,16000,2))
                    self.assertEqual(audio.getnframes(),row['wav']['frames'])
                    frames=audio.readframes(audio.getnframes())
                samples=struct.unpack('<'+'h'*(len(frames)//2),frames)
                self.assertGreater(max(abs(sample) for sample in samples),100)
                self.assertTrue(row['expected_text'])


if __name__=='__main__':unittest.main()

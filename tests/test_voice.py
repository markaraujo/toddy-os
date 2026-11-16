"""Actual process controls with synthetic WAV/STT/TTS fixtures; no audio device use."""
from dataclasses import replace
import hashlib
import os
from pathlib import Path
import tempfile
import threading
import time
import unittest

from runtime.voice.artifacts import Artifact, Consent, VoiceError
from runtime.voice.process import ProcessRunner
from runtime.voice.session import VoiceSession

ROOT=Path(__file__).resolve().parents[1]


class VoiceTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.notice=self.root/'FIXTURE_LICENSE'
        self.notice.write_text('Synthetic test fixture, local tests only.\n')
        self.notice.chmod(0o600)
        self.artifacts={}
        for role,name,kind in [('capture','capture','engine'),('playback','playback','engine'),
                               ('stt-engine','whisper','engine'),('stt-model','stt-model','stt-model'),
                               ('tts-engine','espeak','engine'),('tts-model','tts-model','tts-model'),
                               ('tts-config','tts-config','tts-config')]:
            path=self.root/name
            path.write_bytes((ROOT/'tests/fixtures/voice/engine.py').read_bytes() if kind=='engine' else b'fixture')
            path.chmod(0o700 if kind=='engine' else 0o600)
            self.artifacts[role]=self.artifact(role,path,kind)
        self.consents={a.artifact_id:Consent(a.sha256,a.license_sha256) for a in self.artifacts.values()}

    def artifact(self,identifier,path,kind='engine'):
        return Artifact(identifier,kind,path,path.stat().st_size,hashlib.sha256(path.read_bytes()).hexdigest(),
            'https://example.invalid/explicit-test-fixture','fixture-1','fixture-only',self.notice,
            hashlib.sha256(self.notice.read_bytes()).hexdigest(),'reviewed-local-use',('en','pt-BR'))

    def session(self,**kwargs):
        return VoiceSession(self.artifacts,self.consents,**kwargs)

    @staticmethod
    def wait(path):
        deadline=time.monotonic()+3
        while not path.exists():
            if time.monotonic()>deadline:
                raise AssertionError('fixture readiness deadline')
            time.sleep(.01)

    def test_no_optional_artifact_means_unavailable_with_working_text_fallback(self):
        session=VoiceSession({}, {})
        result=session.capabilities('pt-BR')
        self.assertFalse(result['push_to_talk'])
        self.assertFalse(result['speech_output'])
        self.assertFalse(result['always_listening'])
        self.assertFalse(result['automatic_download'])
        self.assertTrue(result['text_available'])
        self.assertEqual(session.state,'idle')

    def test_en_pt_push_to_talk_release_returns_untrusted_reviewable_text(self):
        for language,expected in [('en','Hello, Toddy.'),('pt-BR','Olá, Toddy.')]:
            with self.subTest(language=language):
                states=[]
                session=self.session(changed=states.append)
                results=[]
                errors=[]
                def work():
                    try: results.append(session.push_to_talk(language,'chosen-microphone'))
                    except Exception as exc: errors.append(exc)
                marker=Path(str(self.artifacts['capture'].path)+'.ready')
                marker.unlink(missing_ok=True)
                worker=threading.Thread(target=work)
                worker.start()
                self.wait(marker)
                session.release_microphone()
                worker.join(timeout=4)
                self.assertFalse(worker.is_alive())
                self.assertEqual(errors,[])
                self.assertEqual(results[0]['text'],expected)
                self.assertTrue(results[0]['untrusted'])
                self.assertTrue(results[0]['requires_review'])
                self.assertEqual(states,['loading','recording','transcribing','transcript-ready'])

    def test_espeak_and_piper_synthesize_and_play_fixture_wav_in_both_languages(self):
        for engine in ['espeak-ng','piper']:
            if engine=='piper':
                path=self.root/'piper'
                path.write_bytes((ROOT/'tests/fixtures/voice/engine.py').read_bytes())
                path.chmod(0o700)
                self.artifacts['tts-engine']=self.artifact('tts-engine',path)
                self.consents['tts-engine']=Consent(self.artifacts['tts-engine'].sha256,
                                                   self.artifacts['tts-engine'].license_sha256)
            for language in ['en','pt-BR']:
                states=[]
                session=self.session(tts_engine=engine,changed=states.append)
                result=session.speak('Private response; not a shell command.',language,'chosen-speaker')
                self.assertEqual(states,['loading','synthesizing','playing','complete'])
                self.assertTrue(result['audio_verified'])
                self.assertEqual(result['tts_engine'],engine)
                self.assertTrue(result['device_playback_requested'])

    def test_missing_consent_license_or_changed_bytes_prevents_launch(self):
        asset=self.artifacts['stt-model']
        with self.assertRaisesRegex(VoiceError,'artifact_consent_required'):
            asset.verify(None)
        with self.assertRaisesRegex(VoiceError,'artifact_metadata'):
            replace(asset,review='unreviewed').verify(self.consents[asset.artifact_id])
        self.notice.write_text('changed notice')
        with self.assertRaises(VoiceError):
            asset.verify(self.consents[asset.artifact_id])
        self.notice.write_text('Synthetic test fixture, local tests only.\n')
        asset.path.write_bytes(b'changed')
        with self.assertRaises(VoiceError):
            asset.verify(self.consents[asset.artifact_id])

    def test_symlink_hardlink_and_world_writable_artifacts_are_refused(self):
        asset=self.artifacts['stt-model']
        alternate=self.root/'alternate'
        alternate.write_bytes(asset.path.read_bytes())
        alternate.chmod(0o600)
        asset.path.unlink()
        asset.path.symlink_to(alternate)
        with self.assertRaisesRegex(VoiceError,'artifact_path'):
            asset.verify(self.consents[asset.artifact_id])
        asset.path.unlink()
        os.link(alternate,asset.path)
        with self.assertRaisesRegex(VoiceError,'artifact_file'):
            asset.verify(self.consents[asset.artifact_id])
        asset.path.unlink()
        asset.path.write_bytes(b'fixture')
        asset.path.chmod(0o666)
        with self.assertRaisesRegex(VoiceError,'artifact_file'):
            asset.verify(self.consents[asset.artifact_id])

    def test_stop_kills_a_nonresponsive_engine_and_prevents_queued_use_until_reset(self):
        path=self.root/'long'
        path.write_bytes((ROOT/'tests/fixtures/voice/engine.py').read_bytes())
        path.chmod(0o700)
        cancel=threading.Event()
        errors=[]
        def work():
            try: ProcessRunner().run([str(path)],cancel=cancel,timeout=5)
            except VoiceError as exc: errors.append(str(exc))
        worker=threading.Thread(target=work)
        worker.start()
        marker=Path(str(path)+'.ready')
        self.wait(marker)
        pid=int(marker.read_text())
        cancel.set()
        worker.join(timeout=3)
        self.assertFalse(worker.is_alive())
        self.assertEqual(errors,['canceled'])
        with self.assertRaises(ProcessLookupError): os.kill(pid,0)
        session=self.session()
        session.stop()
        with self.assertRaisesRegex(VoiceError,'canceled'):
            session.speak('Do not start.','en','chosen-speaker')
        session.reset()
        self.assertTrue(session.speak('Explicit next action.','en','chosen-speaker',play=False)['audio_verified'])

    def test_stop_during_capture_prevents_transcription_and_a_second_voice_writer(self):
        states=[]
        session=self.session(changed=states.append)
        errors=[]
        def work():
            try: session.push_to_talk('pt-BR','chosen-microphone')
            except VoiceError as exc: errors.append(str(exc))
        worker=threading.Thread(target=work)
        worker.start()
        self.wait(Path(str(self.artifacts['capture'].path)+'.ready'))
        try:
            with self.assertRaisesRegex(VoiceError,'voice_busy'):
                session.speak('Do not overlap.','en','chosen-speaker')
        finally:
            session.stop()
            worker.join(timeout=3)
        self.assertFalse(worker.is_alive())
        self.assertEqual(errors,['canceled'])
        self.assertIn('stopping',states)
        self.assertEqual(states[-1],'canceled')
        self.assertNotIn('transcribing',states)

    def test_stop_during_playback_keeps_text_available(self):
        path=self.root/'long'
        path.write_bytes((ROOT/'tests/fixtures/voice/engine.py').read_bytes())
        path.chmod(0o700)
        self.artifacts['playback']=self.artifact('playback',path)
        self.consents['playback']=Consent(self.artifacts['playback'].sha256,
                                          self.artifacts['playback'].license_sha256)
        states=[]
        session=self.session(changed=states.append)
        errors=[]
        def work():
            try: session.speak('Retain this text.','en','chosen-speaker')
            except VoiceError as exc: errors.append(str(exc))
        worker=threading.Thread(target=work)
        worker.start()
        self.wait(Path(str(path)+'.ready'))
        session.stop()
        worker.join(timeout=3)
        self.assertFalse(worker.is_alive())
        self.assertEqual(errors,['canceled'])
        self.assertIn('playing',states)
        self.assertEqual(states[-1],'canceled')
        self.assertTrue(session.capabilities('en')['text_available'])

    def test_truncated_audio_never_counts_as_successful_engine_output(self):
        import wave
        path=self.root/'bad.wav'
        with wave.open(str(path),'wb') as audio:
            audio.setnchannels(1)
            audio.setsampwidth(2)
            audio.setframerate(16000)
            audio.writeframes(b'\x00\x00'*100)
        path.chmod(0o600)
        data=path.read_bytes()
        path.write_bytes(data[:-10])
        with self.assertRaisesRegex(VoiceError,'truncated_audio'):
            VoiceSession._wav(path,capture=True)

    def test_failed_state_observer_never_activates_capture_or_leaks_its_message(self):
        def broken(_state):
            raise RuntimeError('private observer content')
        session=self.session(changed=broken)
        with self.assertRaisesRegex(VoiceError,'voice_observer_failed') as result:
            session.push_to_talk('en','chosen-microphone')
        self.assertNotIn('private',str(result.exception))
        self.assertFalse(Path(str(self.artifacts['capture'].path)+'.ready').exists())
        session.changed=lambda _:None
        session.reset()
        self.assertTrue(session.speak('A new explicit action.','en','chosen-speaker',play=False)['audio_verified'])

    def test_output_bound_and_deadline_do_not_become_success(self):
        for name,timeout,reason in [('spam',5,'engine_output_limit'),('long',.1,'voice_deadline')]:
            path=self.root/name
            path.write_bytes((ROOT/'tests/fixtures/voice/engine.py').read_bytes())
            path.chmod(0o700)
            with self.subTest(name=name),self.assertRaisesRegex(VoiceError,reason):
                ProcessRunner().run([str(path)],cancel=threading.Event(),timeout=timeout)

    def test_invalid_device_and_role_never_start_microphone(self):
        for device in ['--remote','bad\nname','']:
            with self.assertRaisesRegex(VoiceError,'invalid_audio_device'):
                self.session().push_to_talk('en',device)
        self.assertFalse(Path(str(self.artifacts['capture'].path)+'.ready').exists())
        session=self.session()
        session.artifacts['stt-model']=self.artifacts['stt-engine']
        with self.assertRaisesRegex(VoiceError,'artifact_role'):
            session.push_to_talk('en','chosen-microphone')


if __name__=='__main__':
    unittest.main()

"""Optional worker-thread speech flow; transcripts require ordinary text review/policy."""
import os
from pathlib import Path
import tempfile
import threading
import wave

from .artifacts import VoiceError
from .process import ProcessRunner

LANGUAGES={'en':('en','en-us'),'pt-BR':('pt','pt-br')}


class VoiceSession:
    def __init__(self, artifacts, consents, *, tts_engine='espeak-ng', changed=lambda _:None,
                 runner=None):
        if tts_engine not in ('piper','espeak-ng'):
            raise VoiceError('unsupported_tts_engine')
        self.artifacts=dict(artifacts)
        self.consents=dict(consents)
        self.tts_engine=tts_engine
        self.changed=changed
        self.runner=runner or ProcessRunner()
        self.cancel=threading.Event()
        self.release=threading.Event()
        self.lock=threading.Lock()
        self.state='idle'

    def _state(self,state):
        self.state=state
        try:
            self.changed(state)
        except Exception:
            raise VoiceError('voice_observer_failed') from None

    def _path(self,role,language):
        artifact=self.artifacts.get(role)
        if artifact is None:
            raise VoiceError('artifact_unavailable')
        expected = 'engine' if role in ('capture','playback','stt-engine','tts-engine') else role
        if artifact.kind != expected:
            raise VoiceError('artifact_role')
        if language not in artifact.languages:
            raise VoiceError('unsupported_voice_language')
        return artifact.verify(self.consents.get(artifact.artifact_id))

    def capabilities(self,language):
        if language not in LANGUAGES:
            raise VoiceError('unsupported_voice_language')
        def ready(roles):
            try:
                for role in roles:
                    self._path(role,language)
                return True
            except VoiceError:
                return False
        tts=['tts-engine']+(['tts-model','tts-config'] if self.tts_engine=='piper' else [])
        return {'language':language,'text_available':True,'always_listening':False,
                'push_to_talk':ready(['capture','stt-engine','stt-model']),
                'speech_output':ready(tts),'playback':ready(['playback']),
                'tts_engine':self.tts_engine,'automatic_download':False}

    def stop(self):
        """Cancel capture/inference/playback; it does not cancel an unrelated task."""
        self.cancel.set()
        if self.state not in ('idle','transcript-ready','complete','failed','canceled'):
            self._state('stopping')

    def reset(self):
        """Explicitly arm a new user action; never reset cancellation in a worker."""
        if not self.lock.acquire(blocking=False):
            raise VoiceError('voice_busy')
        try:
            self.cancel.clear()
            self.release.clear()
            self._state('idle')
        finally:
            self.lock.release()

    def release_microphone(self):
        """Explicit push-to-talk release ends capture; Stop cancels the whole flow."""
        self.release.set()

    @staticmethod
    def _device(device):
        if not isinstance(device,str) or not 0 < len(device)<=128 or device.startswith('-') or \
                any(ord(char)<32 for char in device):
            raise VoiceError('invalid_audio_device')
        return device

    @staticmethod
    def _wav(path, *, capture=False):
        info=Path(path).lstat()
        if not Path(path).is_file() or Path(path).is_symlink() or info.st_uid!=os.getuid() or \
                info.st_nlink!=1 or info.st_mode & 0o077 or info.st_size>24*1024**2:
            raise VoiceError('invalid_audio')
        try:
            with wave.open(str(path),'rb') as audio:
                if audio.getcomptype()!='NONE' or audio.getsampwidth()!=2 or \
                        audio.getnchannels() not in (1,2) or not 8000<=audio.getframerate()<=48000 or \
                        not 0<audio.getnframes()<=audio.getframerate()*(30 if capture else 120) or \
                        (capture and (audio.getframerate()!=16000 or audio.getnchannels()!=1)):
                    raise VoiceError('invalid_audio')
                expected=audio.getnframes()*audio.getnchannels()*2
                if len(audio.readframes(audio.getnframes()))!=expected:
                    raise VoiceError('truncated_audio')
        except (wave.Error,EOFError,OSError) as exc:
            raise VoiceError('invalid_audio') from exc

    def _run(self,argv,*,release=None,timeout=30):
        return self.runner.run(argv,cancel=self.cancel,release=release,timeout=timeout)

    def _begin(self,language):
        if language not in LANGUAGES:
            raise VoiceError('unsupported_voice_language')
        if not self.lock.acquire(blocking=False):
            raise VoiceError('voice_busy')
        try:
            if self.cancel.is_set():
                raise VoiceError('canceled')
            self._state('loading')
        except Exception:
            self.lock.release()
            raise

    def _failed(self,exc):
        self._state('canceled' if isinstance(exc,VoiceError) and str(exc)=='canceled' else 'failed')

    def push_to_talk(self,language,device):
        """Call from a worker only after explicit microphone selection/press.

        Return untrusted transcript for user review. This never dispatches tools,
        grants authority or sends audio/text to an external provider.
        """
        self._begin(language)
        try:
            capture=self._path('capture',language)
            engine=self._path('stt-engine',language)
            model=self._path('stt-model',language)
            device=self._device(device)
            with tempfile.TemporaryDirectory(prefix='toddy-voice-') as directory:
                audio=Path(directory)/'capture.wav'
                output=Path(directory)/'transcript'
                if self.cancel.is_set():raise VoiceError('canceled')
                self._state('recording')
                result=self._run([capture,'--target',device,'--rate','16000','--channels','1',
                    '--format','s16',str(audio)],release=self.release,timeout=30)
                if not result.released:
                    raise VoiceError('capture_ended_before_release')
                self._wav(audio,capture=True)
                self._state('transcribing')
                self._run([engine,'--model',model,'--file',str(audio),'--language',LANGUAGES[language][0],
                    '--output-txt','--output-file',str(output),'--no-prints','--no-timestamps'],timeout=120)
                transcript=Path(str(output)+'.txt')
                info=transcript.lstat()
                if transcript.is_symlink() or not transcript.is_file() or info.st_size>16384 or \
                        info.st_uid!=os.getuid() or info.st_nlink!=1 or info.st_mode & 0o077:
                    raise VoiceError('transcript_bound')
                text=transcript.read_text(encoding='utf-8').strip()
                if not text or len(text.encode('utf-8'))>16384:
                    raise VoiceError('empty_transcript')
                self._state('transcript-ready')
                return {'text':text,'language':language,'untrusted':True,'requires_review':True,
                        'dispatch':'shared-text-policy','capture_seconds':result.elapsed_seconds}
        except Exception as exc:
            self._failed(exc)
            if isinstance(exc,VoiceError):
                raise
            raise VoiceError('voice_io_failure') from None
        finally:
            self.lock.release()

    def speak(self,text,language,device,*,play=True):
        """Synthesize/play an explicit response on demand; keep text UI independent."""
        self._begin(language)
        try:
            if not isinstance(text,str) or not 0<len(text.encode('utf-8'))<=16384:
                raise VoiceError('speech_text_bound')
            engine=self._path('tts-engine',language)
            device=self._device(device)
            with tempfile.TemporaryDirectory(prefix='toddy-voice-') as directory:
                source=Path(directory)/'response.txt'
                fd=os.open(source,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
                with os.fdopen(fd,'w',encoding='utf-8') as stream:
                    stream.write(text)
                audio=Path(directory)/'response.wav'
                if self.cancel.is_set():raise VoiceError('canceled')
                self._state('synthesizing')
                if self.tts_engine=='piper':
                    model=self._path('tts-model',language)
                    config=self._path('tts-config',language)
                    argv=[engine,'--model',model,'--config',config,'--input-file',str(source),
                          '--output-file',str(audio)]
                else:
                    argv=[engine,'-v',LANGUAGES[language][1],'-f',str(source),'-w',str(audio)]
                result=self._run(argv,timeout=120)
                self._wav(audio)
                if play:
                    player=self._path('playback',language)
                    if self.cancel.is_set():raise VoiceError('canceled')
                    self._state('playing')
                    self._run([player,'--target',device,str(audio)],timeout=120)
                self._state('complete')
                return {'language':language,'tts_engine':self.tts_engine,'audio_verified':True,
                        'device_playback_requested':play,'synthesis_seconds':result.elapsed_seconds,
                        'text_available':True}
        except Exception as exc:
            self._failed(exc)
            if isinstance(exc,VoiceError):
                raise
            raise VoiceError('voice_io_failure') from None
        finally:
            self.lock.release()

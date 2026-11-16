"""Actual native process-loss/reap and file-only engines; never opens devices."""
import hashlib,importlib.util,json,sys,unittest,threading,os,tempfile,time
from pathlib import Path
base=Path('/src/qualification/process-runtime')
sys.path.insert(0,str(base))
spec=importlib.util.spec_from_file_location('native_voice_process_tests',base/'tests/test_voice_process.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(module))
if not result.wasSuccessful() or result.skipped or result.testsRun<3:raise SystemExit('Native process qualification failed or skipped')
files={name:hashlib.sha256((base/'runtime/voice'/name).read_bytes()).hexdigest() for name in ('process.py','child.py','artifacts.py','session.py')}
from runtime.voice.artifacts import Artifact,Consent,VoiceError
from runtime.voice.session import VoiceSession
from runtime.voice.process import ProcessRunner

def artifact(role,path,notice,version,license_id,url):
    p=Path(path);n=Path(notice)
    return Artifact('qualified-'+role,'stt-model' if role=='stt-model' else 'engine',p,p.stat().st_size,hashlib.sha256(p.read_bytes()).hexdigest(),url,version,license_id,n,hashlib.sha256(n.read_bytes()).hexdigest(),'reviewed-local-use',('en','pt-BR'))
a={
 'tts-engine':artifact('tts-engine','/usr/bin/espeak-ng','/usr/share/doc/espeak-ng/COPYING','1.52.0','GPL-3.0-or-later','https://github.com/espeak-ng/espeak-ng'),
 'stt-engine':artifact('stt-engine','/usr/bin/whisper-cli','/usr/share/doc/whisper-cpp/LICENSE','1.9.5','MIT','https://github.com/ggml-org/whisper.cpp'),
 'stt-model':artifact('stt-model','/usr/share/toddy/voice/models/ggml-base.bin','/usr/share/doc/toddy-voice-model-base/whisper-original-license.txt','5359861c739e955e79d9a303bcbc70fb988958b1','MIT','https://huggingface.co/ggerganov/whisper.cpp')}
session=VoiceSession(a,{value.artifact_id:Consent(value.sha256,value.license_sha256) for value in a.values()})
file_sessions={}
os.umask(0o077)
for locale,text in [('en','The quick brown fox jumps over the lazy dog.'),('pt-BR','Onde fica o banheiro?')]:
    session.reset();tts=session.speak(text,locale,'qualification-file-only',play=False)
    with tempfile.TemporaryDirectory() as directory:
        prefix=Path(directory)/'transcript'
        session.reset()
        actual=session.runner.run([session._path('stt-engine',locale),'--model',session._path('stt-model',locale),'--file','/src/qualification/human/'+locale+'.wav','--language','en' if locale=='en' else 'pt','--output-txt','--output-file',str(prefix),'--no-prints','--no-timestamps'],cancel=session.cancel,timeout=120)
        transcript=Path(str(prefix)+'.txt').read_text().strip()
        sys.path.insert(0,'/src/qualification');from consumer import word_error
        error=word_error(text,transcript)
        if error>.4:raise SystemExit('Actual ProcessRunner native transcript mismatch')
    file_sessions[locale]={'tts':tts,'transcript':transcript,'word_error_rate':error,'stt_seconds':actual.elapsed_seconds}
# Explicit Stop against the real native Whisper child, with all artifact hashes
# checked before arming cancellation. This does not record or play anything.
engine=session._path('stt-engine','en');model=session._path('stt-model','en')
session.reset();stop=threading.Timer(.2,session.stop);started=time.monotonic();stop.start()
try:
    session.runner.run([engine,'--model',model,'--file','/src/qualification/human/en.wav','--language','en','--threads','1','--no-prints','--no-timestamps'],cancel=session.cancel,timeout=120)
    raise SystemExit('Native Whisper completed before Stop; no Stop qualification')
except VoiceError as error:
    if str(error)!='canceled':raise
    stop_result={'code':str(error),'seconds':time.monotonic()-started,'engine_sha256':a['stt-engine'].sha256,'scope':'Actual fixed native Whisper process canceled; no model-selected executable or audio device'}
finally:
    stop.cancel();stop.join()
transport={}
for name,path in [('capture','/usr/lib/toddy/voice/pw-record'),('playback','/usr/lib/toddy/voice/pw-play'),('device-list','/usr/bin/pw-dump'),('pw-cat','/usr/bin/pw-cat')]:
    run=ProcessRunner().run([path,'--help'],cancel=threading.Event(),timeout=5)
    p=Path(path);transport[name]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size,'help_seconds':run.elapsed_seconds,'scope':'Actual native no-device help invocation only; no session/device/PTT/playback proof'}
Path('/build/process-qualified.json').write_text(json.dumps({'scope':'Actual native UID101 direct trusted process parent-loss/Stop/reap tests; no escaped-session containment or audio-device claim','tests_run':result.testsRun,'failures':0,'errors':0,'skipped':0,'files':files,'file_sessions':file_sessions,'transport':transport,'native_engine_stop':stop_result},indent=2)+'\n')

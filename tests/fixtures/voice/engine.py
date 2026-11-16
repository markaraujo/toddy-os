#!/usr/bin/python3
"""Synthetic audio/transcript process fixture. It is not a speech engine."""
import os
from pathlib import Path
import signal
import sys
import time
import wave

name=Path(sys.argv[0]).name
args=sys.argv[1:]


def output(flag):
    return Path(args[args.index(flag)+1])


def wav(path,rate=16000):
    with wave.open(str(path),'wb') as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(rate)
        audio.writeframes(b'\x00\x00'*1600)


if name=='capture':
    released=False
    def release(*_):
        global released
        released=True
    signal.signal(signal.SIGINT,release)
    Path(__file__+'.ready').write_text('ready')
    while not released:
        time.sleep(.01)
    wav(Path(args[-1]))
elif name=='whisper':
    language=args[args.index('--language')+1]
    transcript=Path(str(output('--output-file'))+'.txt')
    transcript.write_text('Olá, Toddy.' if language=='pt' else 'Hello, Toddy.',encoding='utf-8')
elif name=='piper':
    assert output('--input-file').read_text(encoding='utf-8')
    assert output('--model').is_file() and output('--config').is_file()
    wav(output('--output-file'),22050)
elif name=='espeak':
    assert output('-f').read_text(encoding='utf-8')
    assert args[args.index('-v')+1] in ('en-us','pt-br')
    wav(output('-w'),22050)
elif name=='playback':
    with wave.open(args[-1],'rb') as audio:
        assert audio.getnframes()>0
elif name=='long':
    signal.signal(signal.SIGTERM,signal.SIG_IGN)
    Path(__file__+'.ready').write_text(str(os.getpid()))
    time.sleep(60)
elif name=='spam':
    os.write(2,b'X'*70000)
else:
    raise AssertionError(name)

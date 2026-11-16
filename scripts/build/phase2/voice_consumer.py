"""Native isolated file-only consumer; never opens an audio device or network."""
import hashlib,json,os,resource,subprocess,sys,time,unicodedata,wave
from pathlib import Path


def words(text):
    return ''.join(c if c.isalnum() else ' ' for c in unicodedata.normalize('NFKD',text.lower()) if not unicodedata.combining(c)).split()


def word_error(reference,actual):
    a,b=words(reference),words(actual)
    if not a or not b:raise ValueError('empty_transcript')
    previous=list(range(len(b)+1))
    for i,x in enumerate(a,1):
        current=[i]
        for j,y in enumerate(b,1):current.append(min(current[-1]+1,previous[j]+1,previous[j-1]+(x!=y)))
        previous=current
    return previous[-1]/len(a)


def timed(argv,log):
    start=time.monotonic()
    # GNU time records this invocation's peak RSS, not a cumulative maximum of
    # previous children. No shell or model-selected command is evaluated.
    metrics=Path(str(log)+'.metrics')
    with log.open('wb') as stream:
        subprocess.run(['/usr/bin/time','-f','%e %M','-o',str(metrics),'--',*argv],stdout=stream,stderr=stream,check=True,timeout=300)
    elapsed,rss=metrics.read_text().split()
    return {'wall_seconds':time.monotonic()-start,'engine_seconds':float(elapsed),'peak_rss_kib':int(rss)}


def consume(component,base=Path('/src'),work=Path('/build'),stage=Path('/stage'),installed=False):
    if os.getuid()!=101:raise ValueError('native_consumer_uid')
    if installed:stage=Path('/')
    result={'scope':'Actual isolated UID101 file-only engine execution; no device/playback/GNOME quality claim','component':component,'samples':{}}
    if component=='whisper-cpp':
        manifest=json.loads((base/'qualification/human/manifest.json').read_text())
        for locale,language in [('en','en'),('pt-BR','pt')]:
            row=manifest['samples'][locale];sample=base/'qualification/human'/f'{locale}.wav'
            if hashlib.sha256(sample.read_bytes()).hexdigest()!=row['wav']['sha256']:raise ValueError('human_sample_integrity')
            prefix=work/f'inference-{locale}'
            metrics=timed([str(stage/'usr/bin/whisper-cli'),'-m',str(base/'qualification/ggml-base.bin'),'-f',str(sample),'-l',language,'-t','8','-nt','-otxt','-of',str(prefix)],work/f'inference-{locale}.log')
            actual=prefix.with_suffix('.txt').read_text().strip()
            error=word_error(row['expected_text'],actual)
            # A short attributed reference is an inference regression, not an
            # intelligibility benchmark. Preserve actual text and measured WER.
            if error>0.4:raise ValueError('human_transcript_word_error')
            result['samples'][locale]={**metrics,'transcript':actual,'reference':row['expected_text'],'word_error_rate':error,'wav_sha256':row['wav']['sha256'],'author':row['author'],'license':row['license']}
    else:
        for locale,voice,text in [('en','en-us','The quick brown fox jumps over the lazy dog.'),('pt-BR','pt-br','Onde fica o banheiro?')]:
            output=work/f'consumer-{locale}.wav'
            # The selected eSpeak engine is built without playback backends.
            prior=os.environ.get('ESPEAK_DATA_PATH');os.environ['ESPEAK_DATA_PATH']=str(stage/'usr/share')
            try:metrics=timed([str(stage/'usr/bin/espeak-ng'),'-v',voice,'-w',str(output),text],work/f'consumer-{locale}.log')
            finally:
                if prior is None:os.environ.pop('ESPEAK_DATA_PATH',None)
                else:os.environ['ESPEAK_DATA_PATH']=prior
            with wave.open(str(output)) as stream:
                if stream.getnchannels()!=1 or stream.getsampwidth()!=2 or not 0<stream.getnframes()<=stream.getframerate()*30:raise ValueError('native_tts_wave')
                if not any(stream.readframes(stream.getnframes())):raise ValueError('native_tts_silent')
            result['samples'][locale]={**metrics,'wav_sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'text':text,'voice':voice}
    (work/('installed-consumer.json' if installed else 'consumer.json')).write_text(json.dumps(result,indent=2)+'\n')
    return result

if __name__=='__main__':consume(sys.argv[1],installed=len(sys.argv)==3 and sys.argv[2]=='installed')

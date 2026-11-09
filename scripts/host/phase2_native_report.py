"""Decode bounded native evidence, retaining exact checksum proof across console noise."""
import base64
import hashlib
import json
import re
import zlib


def decode(serial):
    chunks={};summaries=[];recovered=[];lines=serial.splitlines()
    for i,line in enumerate(lines):
        marker='TODDY_B02_RUNTIME_DATA '
        fragment=None
        if marker in line:fragment=line.split(marker,1)[1]
        elif line.startswith('DY_B02_RUNTIME_DATA '):
            assert i>0 and re.search(r'python3\[\d+\]: TOD\[\s*[0-9.]+\] python3 \(\d+\) used greatest stack depth:',lines[i-1])
            fragment=line.removeprefix('DY_B02_RUNTIME_DATA ')
            recovered.append({'line':i+1,'payload_bytes_changed':0,'reason':'Exact marker split by kernel stack-depth printk'})
        if fragment is not None:
            number,value=fragment.split(' ',1);index=int(number)
            interrupted=re.fullmatch(r'([A-Za-z0-9+/=]+)\[\s*[0-9]+\.[0-9]+\] (clocksource: Watchdog remote CPU [0-9]+ read timed out|systemd-shutdown\[[0-9]+\]: Syncing filesystems and block devices\.)',value)
            if interrupted:
                assert i+1<len(lines) and re.fullmatch(r'[A-Za-z0-9+/=]+',lines[i+1])
                value=interrupted[1]+lines[i+1]
                assert len(value)==1024, 'Only one complete protocol chunk may be rejoined'
                cause='watchdog' if interrupted[2].startswith('clocksource:') else 'shutdown-sync'
                recovered.append({'line':i+1,'payload_bytes_changed':0,'reason':'Exact '+cause+' printk split a complete base64 chunk; concatenate original fragments, verify full report SHA256'})
            assert 0<=index<4096 and 0<len(value)<=1024 and re.fullmatch(r'[A-Za-z0-9+/=]+',value)
            assert index not in chunks or chunks[index]==value,'Conflicting evidence chunk'
            chunks[index]=value
        if 'TODDY_B02_RUNTIME_RESULT ' in line:
            summaries.append(json.loads(line.split('TODDY_B02_RUNTIME_RESULT ',1)[1]))
    assert summaries and all(s==summaries[0] for s in summaries),'No consistent native result'
    summary=summaries[0];assert 0<summary['chunks']<=4096
    assert set(chunks)==set(range(summary['chunks'])),'Missing native evidence'
    packed=base64.b64decode(''.join(chunks[i] for i in range(len(chunks))),validate=True)
    decoder=zlib.decompressobj();raw=decoder.decompress(packed,4*1024**2+1)
    assert len(raw)<=4*1024**2 and decoder.eof and not decoder.unused_data
    assert hashlib.sha256(raw).hexdigest()==summary['report_sha256'],'Native evidence checksum mismatch'
    report=json.loads(raw);assert isinstance(report,dict)
    return report,summary,recovered

"""File-only conversion of reviewed human samples; never opens an audio device.

Uses host libsndfile/libsamplerate, records exact versions and output hashes. This
is fixture preparation, not native inference/audio qualification or a product SDK.
"""
import argparse
import ctypes as c
import ctypes.util
import hashlib
import json
from pathlib import Path
import struct
import wave


class SFInfo(c.Structure):
    _fields_=[('frames',c.c_longlong),('samplerate',c.c_int),('channels',c.c_int),
              ('format',c.c_int),('sections',c.c_int),('seekable',c.c_int)]


class SRCData(c.Structure):
    _fields_=[('data_in',c.POINTER(c.c_float)),('data_out',c.POINTER(c.c_float)),
              ('input_frames',c.c_long),('output_frames',c.c_long),
              ('input_frames_used',c.c_long),('output_frames_gen',c.c_long),
              ('end_of_input',c.c_int),('src_ratio',c.c_double)]


def convert(source,destination):
    if destination.exists() or destination.is_symlink():raise ValueError('fresh_fixture_required')
    snd=c.CDLL(ctypes.util.find_library('sndfile'));res=c.CDLL(ctypes.util.find_library('samplerate'))
    snd.sf_open.argtypes=[c.c_char_p,c.c_int,c.POINTER(SFInfo)];snd.sf_open.restype=c.c_void_p
    snd.sf_readf_float.argtypes=[c.c_void_p,c.POINTER(c.c_float),c.c_longlong];snd.sf_readf_float.restype=c.c_longlong
    snd.sf_close.argtypes=[c.c_void_p];snd.sf_version_string.restype=c.c_char_p
    res.src_simple.argtypes=[c.POINTER(SRCData),c.c_int,c.c_int];res.src_simple.restype=c.c_int
    res.src_get_version.restype=c.c_char_p
    info=SFInfo();handle=snd.sf_open(str(source).encode(),0x10,c.byref(info))
    if not handle:raise ValueError('fixture_decode_failed')
    try:
        if not 1<=info.channels<=2 or not 8000<=info.samplerate<=192000 or not 0<info.frames<=info.samplerate*30:
            raise ValueError('fixture_audio_bound')
        original=(c.c_float*(info.frames*info.channels))()
        if snd.sf_readf_float(handle,original,info.frames)!=info.frames:raise ValueError('fixture_decode_truncated')
    finally:snd.sf_close(handle)
    mono=(c.c_float*info.frames)(*(sum(original[i*info.channels+j] for j in range(info.channels))/info.channels for i in range(info.frames)))
    capacity=int(info.frames*16000/info.samplerate)+512;output=(c.c_float*capacity)()
    job=SRCData(mono,output,info.frames,capacity,0,0,1,16000/info.samplerate)
    if res.src_simple(c.byref(job),0,1)!=0 or job.input_frames_used!=info.frames:
        raise ValueError('fixture_resample_failed')
    samples=[max(-32768,min(32767,round(output[i]*32768))) for i in range(job.output_frames_gen)]
    with wave.open(str(destination),'wb') as target:
        target.setnchannels(1);target.setsampwidth(2);target.setframerate(16000)
        target.writeframes(struct.pack('<'+'h'*len(samples),*samples))
    data=destination.read_bytes()
    return {'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'frames':len(samples),
        'seconds':len(samples)/16000,'format':'PCM16 LE mono16000Hz',
        'conversion':'Decode original Ogg; average channels to mono; libsamplerate SINC_BEST_QUALITY to16kHz; clamp/round to PCM16',
        'libsndfile':snd.sf_version_string().decode(),'libsamplerate':res.src_get_version().decode()}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source',type=Path);parser.add_argument('destination',type=Path)
    args=parser.parse_args();print(json.dumps(convert(args.source,args.destination),sort_keys=True))

if __name__=='__main__':main()

"""Real native GI image decoding with the BWRAP selector, plus malformed refusal."""
import os
from pathlib import Path
import struct
import zlib

import gi
gi.require_version('Gly','2')
from gi.repository import Gly,GLib


def chunk(kind,data):
    return struct.pack('!I',len(data))+kind+data+struct.pack('!I',zlib.crc32(kind+data)&0xffffffff)


assert os.geteuid()==101
status=Path('/proc/self/status').read_text()
assert 'NoNewPrivs:\t1' in status and 'CapEff:\t0000000000000000' in status
png=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('!IIBBBBB',2,1,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(b'\0'+bytes([16,32,64])*2))+chunk(b'IEND',b'')
svg=b'<svg xmlns="http://www.w3.org/2000/svg" width="2" height="1"><path fill="#102040" d="M0 0h2v1H0z"/></svg>'
for data,mime in [(png,'image/png'),(svg,'image/svg+xml')]:
    loader=Gly.Loader.new_for_bytes(GLib.Bytes.new(data))
    loader.set_sandbox_selector(Gly.SandboxSelector.BWRAP)
    image=loader.load();assert image.get_mime_type()==mime
    frame=image.next_frame();assert (frame.get_width(),frame.get_height())==(2,1)
    pixels=frame.get_buf_bytes().get_data()
    formats={Gly.MemoryFormat.R8G8B8:(3,[16,32,64]),
             Gly.MemoryFormat.R8G8B8A8:(4,[16,32,64,255]),
             Gly.MemoryFormat.R8G8B8A8_PREMULTIPLIED:(4,[16,32,64,255]),
             Gly.MemoryFormat.B8G8R8A8:(4,[64,32,16,255]),
             Gly.MemoryFormat.B8G8R8A8_PREMULTIPLIED:(4,[64,32,16,255])}
    size,expected=formats[frame.get_memory_format()]
    assert list(pixels[:size*2])==expected*2,(mime,list(pixels),frame.get_memory_format())
    print(mime,'native bwrap image2x1 navy pixels0',flush=True)
for data in [b'not-an-image',png[:25]]:
    loader=Gly.Loader.new_for_bytes(GLib.Bytes.new(data))
    loader.set_sandbox_selector(Gly.SandboxSelector.BWRAP)
    try:
        image=loader.load()
        image.next_frame()
    except GLib.Error:
        print('malformed image refused',flush=True)
    else:raise AssertionError('Malformed image unexpectedly decoded')

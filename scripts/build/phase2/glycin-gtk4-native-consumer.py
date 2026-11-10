"""Actual sandboxed image to GDK texture and PNG roundtrip, no display claim."""
import os,struct,zlib,json
from pathlib import Path
import gi
gi.require_version('Gly','2');gi.require_version('GlyGtk4','2')
from gi.repository import Gly,GlyGtk4,GLib
assert os.geteuid()==101
status=Path('/proc/self/status').read_text()
assert 'NoNewPrivs:\t1' in status and 'CapEff:\t0000000000000000' in status
assert 'GLYCIN_DATA_DIR' not in os.environ, 'Use owned installed loader configuration'
def chunk(kind,data):
 return struct.pack('!I',len(data))+kind+data+struct.pack('!I',zlib.crc32(kind+data)&0xffffffff)
png=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('!IIBBBBB',2,1,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(b'\0'+bytes([16,32,64])*2))+chunk(b'IEND',b'')
svg=b'<svg xmlns="http://www.w3.org/2000/svg" width="2" height="1"><path fill="#102040" d="M0 0h2v1H0z"/></svg>'
def load(data):
 loader=Gly.Loader.new_for_bytes(GLib.Bytes.new(data));loader.set_sandbox_selector(Gly.SandboxSelector.BWRAP)
 return loader.load().next_frame()
def pixels(frame):
 assert (frame.get_width(),frame.get_height())==(2,1)
 formats={Gly.MemoryFormat.R8G8B8:(3,[16,32,64]),Gly.MemoryFormat.R8G8B8A8:(4,[16,32,64,255]),Gly.MemoryFormat.R8G8B8A8_PREMULTIPLIED:(4,[16,32,64,255]),Gly.MemoryFormat.B8G8R8A8:(4,[64,32,16,255]),Gly.MemoryFormat.B8G8R8A8_PREMULTIPLIED:(4,[64,32,16,255])}
 size,expected=formats[frame.get_memory_format()];assert list(frame.get_buf_bytes().get_data()[:size*2])==expected*2
for cycle in range(2):
 for data in [png,svg]:
  frame=load(data);pixels(frame);texture=GlyGtk4.frame_get_texture(frame)
  assert (texture.get_width(),texture.get_height())==(2,1)
  encoded=texture.save_to_png_bytes().get_data();assert encoded.startswith(b'\x89PNG\r\n\x1a\n');pixels(load(encoded))
 try:load(b'not-an-image')
 except GLib.Error:pass
 else:raise AssertionError('Malformed image accepted')
 pixels(load(png))
print(json.dumps({'sandbox':'BWRAP','installed_default_loader_paths':True,'source_image_pixel_cases':4,'GDK_texture_PNG_pixel_roundtrips':4,'malformed_refusals':2,'recovery_cycles':2,'display_or_widgets_tested':False}))

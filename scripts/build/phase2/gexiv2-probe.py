"""Own local GI consumer; real PNG metadata writes, pixel retention and refusal."""
from pathlib import Path
import hashlib,json,struct,sys,zlib
import gi
gi.require_version('GExiv2','0.16')
from gi.repository import GExiv2,GLib
base=Path(sys.argv[1]);base.mkdir(exist_ok=False)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def chunk(t,b):return struct.pack('>I',len(b))+t+b+struct.pack('>I',zlib.crc32(t+b)&0xffffffff)
png=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',1,1,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(b'\0\x12\x34\x56'))+chunk(b'IEND',b'')
def image(p):
 data=p.read_bytes();assert data[:8]==png[:8];i=8;keep=[]
 while i<len(data):
  n=struct.unpack('>I',data[i:i+4])[0];t=data[i+4:i+8];raw=data[i:i+n+12];assert len(raw)==n+12
  assert zlib.crc32(raw[4:-4])&0xffffffff==struct.unpack('>I',raw[-4:])[0]
  if t in [b'IHDR',b'IDAT',b'IEND']:keep.append(raw)
  i+=n+12
 assert i==len(data);return keep
for cycle in range(2):
 p=base/('image-'+str(cycle)+'.png');p.write_bytes(png);pixels=image(p)
 m=GExiv2.Metadata();m.open_path(str(p));assert (m.get_pixel_width(),m.get_pixel_height())==(1,1)
 key='Xmp.dc.title';value='Olá Toddy — recuperação '+str(cycle)
 assert m.try_set_tag_string(key,value);m.save_file(str(p))
 r=GExiv2.Metadata();r.open_path(str(p));assert r.try_get_tag_string(key)=='lang="x-default" '+value and image(p)==pixels
 assert r.try_clear_tag(key);r.save_file(str(p));reset=GExiv2.Metadata();reset.open_path(str(p));assert not reset.has_tag(key) and image(p)==pixels
 bad=base/('bad-'+str(cycle)+'.jpg');bad.write_bytes(b'\xff\xd8\xff\xe1\x00\x20Exif\x00\x00truncated');before=sha(bad);good=sha(p)
 try:GExiv2.Metadata().open_path(str(bad))
 except GLib.Error:pass
 else:raise AssertionError('Malformed JPEG accepted')
 assert sha(bad)==before and sha(p)==good
 recovered=GExiv2.Metadata();recovered.open_path(str(p));assert recovered.get_pixel_width()==1 and not recovered.has_tag(key)
print(json.dumps({'GI_namespace':'GExiv2-0.16','UTF8_PNG_metadata_write_read_reset_cycles':2,'image_chunks_retained':True,'malformed_JPEG_refusals':2,'inputs_unchanged_on_refusal':True,'recovery_cycles':2}))

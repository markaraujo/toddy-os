"""Local metadata edit/read/reset and corrupt-file refusal with pixel data retained."""
from pathlib import Path
import hashlib,json,os,struct,subprocess,sys,zlib
binary=sys.argv[1];root=Path(sys.argv[2]);root.mkdir()
def chunk(kind,data):return struct.pack('!I',len(data))+kind+data+struct.pack('!I',zlib.crc32(kind+data)&0xffffffff)
png=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('!IIBBBBB',2,1,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(b'\0'+bytes([16,32,64])*2))+chunk(b'IEND',b'')
def pixels(path):
 data=path.read_bytes();assert data.startswith(b'\x89PNG\r\n\x1a\n');offset=8;out=[]
 while offset<len(data):
  size=struct.unpack('!I',data[offset:offset+4])[0];kind=data[offset+4:offset+8];body=data[offset+8:offset+8+size];assert offset+12+size<=len(data)
  if kind in (b'IHDR',b'IDAT',b'IEND'):out.append((kind.hex(),hashlib.sha256(body).hexdigest()))
  offset+=12+size
 assert offset==len(data);return out
def run(args,ok=0):
 r=subprocess.run([binary,*args],capture_output=True,text=True,timeout=10);assert r.returncode==ok,(args,r.returncode,r.stdout,r.stderr);return r
assert '0.28.8' in run(['--version']).stdout
for cycle in range(2):
 image=root/('image-'+str(cycle)+'.png');image.write_bytes(png);before=pixels(image)
 run(['-M','set Exif.Image.Artist Toddy ã',str(image)])
 assert run(['-K','Exif.Image.Artist','-Pv',str(image)]).stdout.strip()=='Toddy ã'
 assert pixels(image)==before
 bad=root/('bad-'+str(cycle)+'.jpg');bad.write_bytes(b'\xff\xd8\xff\xe1\x00\x04EX');original=bad.read_bytes()
 r=subprocess.run([binary,str(bad)],capture_output=True,text=True,timeout=10);assert r.returncode!=0 and bad.read_bytes()==original
 assert run(['-K','Exif.Image.Artist','-Pv',str(image)]).stdout.strip()=='Toddy ã'
 run(['-M','del Exif.Image.Artist',str(image)])
 absent=run(['-K','Exif.Image.Artist','-Pv',str(image)],ok=1);assert absent.stdout==absent.stderr=='' and pixels(image)==before
# Positive XMP parser control followed by an external-entity read-denial canary.
canary=root/'synthetic-canary.txt';sentinel='TODDY-SYNTHETIC-XMP-CANARY';canary.write_text(sentinel)
body='<x:xmpmeta xmlns:x="adobe:ns:meta/"><rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"><rdf:Description rdf:about="" xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:source>VALUE</dc:source></rdf:Description></rdf:RDF></x:xmpmeta>'
header='<?xpacket begin="" id="W5M0MpCehiHzreSzNTczkc9d"?>'
valid_xmp=root/'valid.xmp';valid_xmp.write_text(header+body.replace('VALUE','TODDY-VALID-XMP')+'<?xpacket end="w"?>')
assert 'TODDY-VALID-XMP' in run(['-K','Xmp.dc.source','-Pv',str(valid_xmp)]).stdout
invalid_xmp=root/'external-entity.xmp';invalid_xmp.write_text(header+'<!DOCTYPE x:xmpmeta [<!ENTITY canary SYSTEM "'+canary.as_uri()+'">]>'+body.replace('VALUE','&canary;')+'<?xpacket end="w"?>')
original=invalid_xmp.read_bytes();r=subprocess.run([binary,'-K','Xmp.dc.source','-Pv',str(invalid_xmp)],capture_output=True,text=True,timeout=10)
assert r.returncode==1 and 'XMP Toolkit error 201: Error in XMLValidator' in r.stderr and 'Failed to decode XMP metadata' in r.stderr and sentinel not in r.stdout+r.stderr and invalid_xmp.read_bytes()==original and canary.read_text()==sentinel
assert 'TODDY-VALID-XMP' in run(['-K','Xmp.dc.source','-Pv',str(valid_xmp)]).stdout
print(json.dumps({'local_PNG_EXIF_UTF8_edit_read_reset_cycles':2,'IDAT_IHDR_IEND_unchanged':True,'corrupt_JPEG_refusals':2,'failed_input_unchanged':True,'recovery_cycles':2,'valid_XMP_parser_control':True,'external_entity_refused_canary_not_read':True,'XMP_recovery':True,'remote_transport_or_GUI_tested':False}))

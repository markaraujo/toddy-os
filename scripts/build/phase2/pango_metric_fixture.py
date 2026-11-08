#!/usr/bin/env python3
"""Portable test-only Boxes metric oracle; never modify Pango runtime code.

Original Boxes lacks lowercase/digits, so hardcoded derived metrics depend on
external fallback fonts. A separate full-ASCII cmap preserves all existing glyph
outlines/advances and gives an independent exact100px advance oracle.
"""
import ctypes
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import struct
import subprocess
import sys
import xml.etree.ElementTree as ET


def digest(data):
    return hashlib.sha256(data).hexdigest()


def checksum(data):
    padded=data+b'\0'*((-len(data))%4)
    return sum(struct.unpack('>'+str(len(padded)//4)+'I',padded))&0xffffffff


def ascii_boxes(original,ttx):
    tree=ET.fromstring(ttx)
    assert int(tree.find('head/unitsPerEm').get('value'))==1024
    glyphs=[g.get('name') for g in tree.find('GlyphOrder')]
    widths={g.get('name'):int(g.get('width')) for g in tree.find('hmtx')}
    assert set(widths.values())=={1024} and glyphs[0]=='.notdef'
    mapping={int(m.get('code'),16):glyphs.index(m.get('name')) for m in tree.findall('cmap/cmap_format_4/map')}
    full={code:mapping.get(code) or glyphs.index('A') for code in range(32,127)}
    assert all(widths[glyphs[gid]]==1024 for gid in full.values())
    groups=b''.join(struct.pack('>III',code,code,gid) for code,gid in full.items())
    subtable=struct.pack('>HHIII',12,0,16+len(groups),0,len(full))+groups
    cmap=struct.pack('>HH',0,2)+struct.pack('>HHI',0,4,20)+struct.pack('>HHI',3,10,20)+subtable
    data=bytearray(original);count=struct.unpack_from('>H',data,4)[0];tables={}
    for i in range(count):
        position=12+16*i;tag,crc,offset,size=struct.unpack_from('>4sIII',data,position)
        assert offset+size<=len(data);tables[tag]=(position,offset,size)
    assert b'cmap' in tables and b'head' in tables and b'maxp' in tables
    assert not {b'kern',b'GSUB',b'GPOS'} & set(tables),'Geometry oracle excludes advance-changing layout tables'
    assert struct.unpack_from('>H',data,tables[b'maxp'][1]+4)[0]==len(glyphs)
    assert struct.unpack_from('>H',data,tables[b'head'][1]+18)[0]==1024
    data.extend(b'\0'*((-len(data))%4));offset=len(data);data.extend(cmap)
    struct.pack_into('>III',data,tables[b'cmap'][0]+4,checksum(cmap),offset,len(cmap))
    head=tables[b'head'][1];struct.pack_into('>I',data,head+8,0)
    struct.pack_into('>I',data,head+8,(0xb1b0afba-checksum(data))&0xffffffff)
    assert checksum(data)==0xb1b0afba
    # Other referenced table bytes are preserved, apart from required head checksum.
    for tag,(_,start,size) in tables.items():
        if tag not in (b'cmap',b'head'):assert data[start:start+size]==original[start:start+size]
    proof={'original_font_sha256':digest(original),'ttx_sha256':digest(ttx),
           'derived_font_sha256':digest(data),'ascii_range':[32,126],
           'glyph_count':len(glyphs),'units_per_em':1024,'advance_units':1024,
           'expected_advance_at_100px_in_pango_units':100*1024,
           'existing_glyph_outlines_unchanged':True,'full_font_checksum':'b1b0afba'}
    return bytes(data),proof


def qualify():
    work=Path('/build');source=Path('/src');directory=work/'metric-oracle'
    assert not directory.exists(),'Reconcile prior oracle run; no replay'
    directory.mkdir()
    library=ctypes.CDLL('/build/compile/pango/libpango-1.0.so.0')
    library.pango_language_from_string.argtypes=[ctypes.c_char_p];library.pango_language_from_string.restype=ctypes.c_void_p
    library.pango_language_get_sample_string.argtypes=[ctypes.c_void_p];library.pango_language_get_sample_string.restype=ctypes.c_char_p
    sample=library.pango_language_get_sample_string(library.pango_language_from_string(b'en'))
    assert sample and all(32<=c<=126 for c in sample),'English metric sample exceeds the independent ASCII oracle'
    original=(source/'tests/fonts/boxes.ttf').read_bytes();ttx=(source/'tests/fonts/boxes.ttx').read_bytes()
    derived,proof=ascii_boxes(original,ttx);font=directory/'boxes-ascii.ttf';font.write_bytes(derived)
    baseline=source/'tests/test-font-data.c';text=baseline.read_text();adapted=text
    old='g_test_build_filename (G_TEST_DIST, "fonts", "boxes.ttf", NULL)'
    assert adapted.count(old)==1
    adapted=adapted.replace(old,'g_strdup ("/build/metric-oracle/boxes-ascii.ttf")')
    assert '.approximate_char_width = 49273,' in adapted and '.approximate_digit_width = 58368,' in adapted
    adapted,count=re.subn(r'\.approximate_(char|digit)_width = [0-9]+,',
                         lambda m:'.approximate_'+m.group(1)+'_width = 100 * PANGO_SCALE,',adapted)
    assert count==2
    code=directory/'test-font-data.c';code.write_text(adapted)
    commands=json.loads((work/'compile/compile_commands.json').read_text())
    rows=[r for r in commands if Path(r['file']).name=='test-font-data.c'];assert len(rows)==1
    row=rows[0];args=list(row.get('arguments') or shlex.split(row['command']))
    old_object=args[args.index('-o')+1];obj=directory/'test-font-data.o'
    for flag,value in [('-o',str(obj)),('-MF',str(obj)+'.d'),('-MQ',str(obj))]:
        if flag in args:args[args.index(flag)+1]=value
    inputs=[i for i,arg in enumerate(args) if arg.endswith('/test-font-data.c')];assert len(inputs)==1
    args[inputs[0]]=str(code)
    subprocess.run(args,cwd=row['directory'],check=True)
    lines=subprocess.run(['ninja','-C',str(work/'compile'),'-t','commands','tests/test-font-data'],capture_output=True,text=True,check=True).stdout.splitlines()
    links=[]
    for line in lines:
        parts=shlex.split(line)
        if '-o' in parts and parts[parts.index('-o')+1]=='tests/test-font-data':links.append(parts)
    assert len(links)==1
    link=links[0];assert not any(a in ('&&',';','|') for a in link)
    assert old_object in link
    link[link.index(old_object)]=str(obj);binary=directory/'test-font-data'
    link[link.index('-o')+1]=str(binary)
    subprocess.run(link,cwd=work/'compile',check=True)
    env=dict(os.environ,LD_LIBRARY_PATH='/build/compile/pango',G_TEST_SRCDIR='/src/tests',
             G_TEST_BUILDDIR='/build/compile/tests',LC_ALL='en_US.UTF-8',
             FONTCONFIG_FILE='/etc/fonts/fonts.conf',XDG_DATA_HOME='/build/test-default-data')
    with (directory/'test.log').open('xb') as output:
        result=subprocess.run([str(binary),'-k','--tap'],env=env,stdout=output,stderr=subprocess.STDOUT)
    log=(directory/'test.log').read_text();(directory/'test.exit').write_text(str(result.returncode)+'\n')
    assert result.returncode==0,'Portable metric oracle failed; preserve original and variant logs'
    assert '1..3' in log and len(re.findall(r'^ok [0-9]+ ',log,re.M))==3
    before=json.loads((work/'font-recovery/before.json').read_text())
    after={p:digest(Path(p).read_bytes()) for p in before};assert before==after
    proof.update({'sample_sha256':digest(sample),'english_sample_is_ascii':True,'original_source_sha256':digest(text.encode()),'adapted_test_sha256':digest(adapted.encode()),
                  'test_exit':result.returncode,'test_log_sha256':digest(log.encode()),
                  'portable_cases_passed':3,'original_compiled_binaries_unchanged':True,
                  'original_binary_sha256':before,'test_binary_sha256':digest(binary.read_bytes()),
                  'scope':'Portable independent font geometry fixture, not a passed original fallback-dependent golden; runtime code/expected own glyph geometry unchanged'})
    (directory/'qualified.json').write_text(json.dumps(proof,indent=2)+'\n')
    print(json.dumps(proof,indent=2))


if __name__=='__main__':
    if sys.argv[1:]==['qualify']:qualify()
    elif len(sys.argv)==5 and sys.argv[1]=='font':
        data,proof=ascii_boxes(Path(sys.argv[2]).read_bytes(),Path(sys.argv[3]).read_bytes())
        with Path(sys.argv[4]).open('xb') as stream:stream.write(data)
        print(json.dumps(proof,indent=2))
    else:raise SystemExit('Use font INPUT_TTF INPUT_TTX OUTPUT or qualify in isolated native target')

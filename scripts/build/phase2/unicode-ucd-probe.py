"""Validate actual Unicode17 scalar records and block ranges without a display."""
from pathlib import Path
import json,sys
p=Path(sys.argv[1])/'usr/share/unicode/ucd';assert 'Version 17.0.0' in (p/'ReadMe.txt').read_text()
records={};previous=-1
for line in (p/'UnicodeData.txt').read_text().splitlines():
    row=line.split(';');assert len(row)==15
    scalar=int(row[0],16);assert previous<scalar<=0x10ffff;previous=scalar;records[scalar]=row
assert records[0x41][1]=='LATIN CAPITAL LETTER A'
assert records[0xe3][1]=='LATIN SMALL LETTER A WITH TILDE'
assert records[0x1f600][1]=='GRINNING FACE'
blocks=[];end=-1
for line in (p/'Blocks.txt').read_text().splitlines():
    line=line.split('#',1)[0].strip()
    if not line:continue
    limits,name=line.split(';',1);first,last=[int(v,16) for v in limits.strip().split('..')]
    assert end<first<=last<=0x10ffff;end=last;blocks.append((first,last,name.strip()))
assert any(first<=0xe3<=last and name=='Latin-1 Supplement' for first,last,name in blocks)
assert 'LATIN SMALL LETTER A WITH TILDE' in (p/'NamesList.txt').read_text()
print(json.dumps({'version':'17.0.0','scalar_records':len(records),'sorted_valid_scalar_fields':True,'block_ranges':len(blocks),'nonoverlapping_blocks':True,'Latin_Portuguese_emoji_metadata':True,'UTF8_names':True,'rendering_or_input_claimed':False}))

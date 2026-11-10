"""Validate the actual typed location database and representative source lookups."""
from pathlib import Path
import hashlib,json,math,sys,xml.etree.ElementTree as ET
from gi.repository import GLib
prefix=Path(sys.argv[1]) if len(sys.argv)>1 else Path('/stage')
xml=prefix/'usr/share/gweather-locations/Locations.xml';data=prefix/'usr/lib/gweather-locations/Locations.bin'
assert xml.is_file() and data.is_file() and xml.stat().st_size<16*1024**2 and data.stat().st_size<16*1024**2
root=ET.parse(xml).getroot();assert root.tag=='gweather' and root.get('format')=='1.0'
counts={tag:len(list(root.iter(tag))) for tag in ['region','country','state','city','location','named-timezone','timezone']}
assert counts=={'region':9,'country':245,'state':254,'city':4349,'location':4002,'named-timezone':2,'timezone':332}
signature='(ta{sq}a{sq}a{s((ss)as)}a((ss)ss(dd)ssqyqqaqaq))'
v=GLib.Variant.new_from_bytes(GLib.VariantType.new(signature),GLib.Bytes.new(data.read_bytes()),False)
assert v.is_normal_form()
magic,countries,metars,zones,locations=v.unpack();assert magic==0x5747687442443130
assert len(locations)==8862 and len(zones)==332 and len(countries)==245
assert set(countries)=={c.findtext('iso-code') for c in root.iter('country')}
assert set(zones)=={t.get('id') for t in root.iter('timezone')}
assert 'America/Sao_Paulo' in zones
for code,index in countries.items():assert 0<=index<len(locations) and locations[index][4]==code and locations[index][7]==2
for code,index in metars.items():assert 0<=index<len(locations) and locations[index][5]==code
for index,loc in enumerate(locations):
 assert len(loc)==12 and 0<=loc[7]<=7
 assert loc[6]==65535 or loc[6]<len(zones)
 assert all(x==65535 or x<len(locations) for x in [loc[8],loc[9]])
 assert all(0<=c<len(locations) and locations[c][9]==index for c in loc[10])
 assert all(0<=z<len(zones) for z in loc[11])
representatives={}
for code in ['SBGR','LPPT']:
 source=next(c for c in root.iter('location') if c.findtext('code')==code);loc=locations[metars[code]]
 expected=tuple(float(s)*math.pi/180 for s in source.findtext('coordinates').split())
 assert all(abs(a-b)<1e-12 for a,b in zip(loc[3],expected))
 assert loc[0][0]==(source.findtext('_name') or source.findtext('name'))
 representatives[code]={'name':loc[0][0],'coordinates_match_source':True}
for code in ['BR','PT']:assert locations[countries[code]][4]==code
print(json.dumps({'normal_form':True,'native_byteorder':sys.byteorder,'locations':len(locations),'countries':len(countries),'timezones':len(zones),'source_counts':counts,'all_index_bounds_and_parent_links':True,'country_BR_PT_lookup':True,'timezone_Sao_Paulo_lookup':True,'representative_airports':representatives,'data_sha256':hashlib.sha256(data.read_bytes()).hexdigest(),'source_XML_sha256':hashlib.sha256(xml.read_bytes()).hexdigest(),'real_owner_location_or_forecast_tested':False}))

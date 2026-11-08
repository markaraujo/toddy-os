"""Native installed country/language JSON and actual Portuguese gettext data."""
import gettext
import json
from pathlib import Path
import sys

prefix=Path(sys.argv[1]) if len(sys.argv)>1 else Path('/')
data=prefix/'usr/share/iso-codes/json'
files=list(data.glob('*.json'));assert len(files)==16
for path in files:assert isinstance(json.loads(path.read_text()),dict)
countries=json.loads((data/'iso_3166-1.json').read_text())['3166-1']
names={r['alpha_2']:r['name'] for r in countries}
assert names['BR']=='Brazil' and names['PT']=='Portugal' and names['US']=='United States'
languages=json.loads((data/'iso_639-3.json').read_text())['639-3']
names2={r['alpha_3']:r['name'] for r in languages}
assert names2['por']=='Portuguese' and names2['eng']=='English'
pt=gettext.translation('iso_3166-1',localedir=prefix/'usr/share/locale',languages=['pt_BR'])
assert pt.gettext('Brazil')=='Brasil' and pt.gettext('Portugal')=='Portugal'
print(json.dumps({'scope':'Real native country/language database and Portuguese translation data, not graphical locale selection',
    'json_files':len(files),'countries':len(countries),'languages':len(languages),'pt_BR_Brazil':pt.gettext('Brazil')}))

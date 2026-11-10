#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/stage-results.json ]]
python3 - <<'PRE'
from pathlib import Path
import hashlib,json
w=Path('/build');r=json.loads((w/'compile-resource.json').read_text());assert r['exit']==0 and not r['interrupted']
assert not list((w/'dictionary-source').glob('*.rws'))
assert (w/'stage/usr/lib/aspell-0.60/iso-8859-1.cset').is_file()
assert not (w/'aspell-resume-2-before.json').exists()
elf={str(p.relative_to(w/'compile')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (w/'compile').rglob('*') if p.is_file() and not p.is_symlink() and p.open('rb').read(4)==b'\x7fELF'}
assert elf
(w/'aspell-resume-2-before.json').write_text(json.dumps(elf,sort_keys=True)+'\n')
PRE
mv /stage/usr/share/info/dir /build/aspell-generated-info-dir
cat > /build/private-bin/aspell <<'WRAPPER'
#!/bin/bash
exec /build/compile/aspell --data-dir=/stage/usr/lib/aspell-0.60 --dict-dir=/build/dictionary-source "$@"
WRAPPER
chmod 755 /build/private-bin/aspell
cp /src/toddy-dictionary-source/{en.dat,en_phonet.dat,en_affix.dat} /stage/usr/lib/aspell-0.60/
cd /build/dictionary-source
ASPELL=/build/private-bin/aspell PREZIP=/build/compile/prezip-bin ./configure
make -j2
make DESTDIR=/stage dictdir=/usr/lib/aspell-0.60 datadir=/usr/lib/aspell-0.60 install
mkdir -p /stage/usr/share/doc/aspell/dictionary-en
cp /src/toddy-dictionary-source/{Copyright,README,README.iso} /stage/usr/share/doc/aspell/dictionary-en/
LD_LIBRARY_PATH=/stage/usr/lib python3 /src/toddy-probe.py /stage /build/consumer > /build/native-consumer.json
python3 - <<'PY'
from pathlib import Path
import hashlib,json,os
w=Path('/build');consumer=json.loads((w/'native-consumer.json').read_text());assert consumer['recovery_cycles']==2 and consumer['CLI_pipe_and_unknown_option']
original=json.loads((w/'dictionary-source-before.json').read_text());assert original=={str(p.relative_to('/src/toddy-dictionary-source')):hashlib.sha256(p.read_bytes()).hexdigest() for p in Path('/src/toddy-dictionary-source').rglob('*') if p.is_file() and not p.is_symlink()}
s=os.statvfs('/build');assert s.f_bavail*s.f_frsize>=16*1024**3
r={'scope':'Frozen Aspell0.60.8.2 optimized shared C/C++ API/CLI with real official English SCOWL2020.12.07 dictionary. Upstream package has no original test suite per frozen book. Own actual C API/CLI known/misspelling/suggestion/UTF8 personal persistence/session clear/malformed dictionary+invalid language/option refusal/input retention/recovery. No Portuguese lexicon, Enchant, Libspelling, editor, GUI or general parser-security acceptance. Readonly source and byte-identical private dictionary build copy, owned Which reused.','compile_exit':0,'stage_exit':0,'original_tests':'No upstream test suite; not reported as a passing original suite.','consumer':consumer,'resource':json.loads((w/'compile-resource.json').read_text()),'artifacts':{str(p.relative_to(w/'compile')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (w/'compile').rglob('*') if p.is_file() and not p.is_symlink() and p.open('rb').read(4)==b'\x7fELF'},'stage_sha256':{str(p.relative_to('/stage')):hashlib.sha256(p.read_bytes()).hexdigest() for p in Path('/stage').rglob('*') if p.is_file() and not p.is_symlink()}}
(w/'stage-results.json').write_text(json.dumps(r,indent=2)+'\n')
PY

python3 - <<'POST'
from pathlib import Path
import hashlib,json
w=Path('/build');before=json.loads((w/'aspell-resume-2-before.json').read_text())
assert before=={str(p.relative_to(w/'compile')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (w/'compile').rglob('*') if p.is_file() and not p.is_symlink() and p.open('rb').read(4)==b'\x7fELF'}
POST

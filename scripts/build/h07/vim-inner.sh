#!/bin/bash
# LFS 13.1-systemd 8.74, security source overlay ADR-0013.
set -euo pipefail
cd /sources/vim-9.2.1201
test ! -e /sources/stage/vim
echo '#define SYS_VIMRC_FILE "/etc/vimrc"' >> src/feature.h
./configure --prefix=/usr
make
chown -R tester:tester .
mkdir -p /sources/evidence/h07-vim
# Keep every upstream test, including optional downloader tests. Missing
# prerequisites must stop for diagnosis, rather than silently removing tests.
install -o tester -g tester -m600 /dev/null /sources/evidence/h07-vim/download-events.jsonl
export TODDY_VIM_DOWNLOAD_LOG=/sources/evidence/h07-vim/download-events.jsonl
unset TEST_FILTER TEST_SKIP_PAT TEST_MAY_FAIL
LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8 TERM=xterm-256color \
 su -s /usr/bin/expect tester <<'EXPECT' > /sources/evidence/h07-vim/check.log 2>&1
set timeout -1
spawn -noecho sh -c {exec 3>&- 4>&-; stty rows 24 cols 80; SHELL=/bin/bash PATH=/sources/test-inputs/vim-glvs/bin:$PATH exec make -j1 test}
expect eof
set result [wait]
if {[lindex $result 2] != 0 || [llength $result] > 4} {exit 125}
exit [lindex $result 3]
EXPECT
python3 - <<'REPORT'
from pathlib import Path
import json,re,subprocess
report=Path('src/testdir/test_result.log').read_text()
assert re.search(r'^\s*Failed:\s+0\s+Tests',report,re.M),report
assert re.search(r'^Executed:\s+[1-9][0-9]*\s+Tests',report,re.M),report
result=subprocess.run(['make','-s','-C','src/testdir','--eval',
 'toddy-required-results:;@printf "%s\\n" $(NEW_TESTS_RES)','toddy-required-results'],capture_output=True,text=True,check=True)
required=result.stdout.splitlines()
assert len(required)>100 and len(set(required))==len(required)
assert all(re.fullmatch(r'test_[A-Za-z0-9_]+\.res',name) for name in required)
missing=[name for name in required if not (Path('src/testdir')/name).is_file()]
assert not missing,missing
Path('/sources/evidence/h07-vim/complete-script-results.json').write_text(json.dumps({'required_result_files':required,'missing':missing,'test_filters_used':False},indent=2)+'\n')
print(report)
REPORT
python3 - <<'VERIFY'
import json
from pathlib import Path
rows=json.loads(Path('/sources/test-inputs/vim-glvs/manifest.json').read_text())['components']
events=[json.loads(l) for l in Path('/sources/evidence/h07-vim/download-events.jsonl').read_text().splitlines()]
assert {r['source_id'] for r in events if r['kind']=='plugin' and r['verified']}=={r['source_id'] for r in rows}
assert all(r['uid']!=0 for r in events)
print('Unmodified GLVS suite used verified live downloads for every frozen plugin')
VERIFY
find . -type f \( -name '*.log' -o -name '*.res' -o -name '*.fail' \) -print0 | \
 tar --null -T - -czf /sources/evidence/h07-vim/test-reports.tar.gz
make DESTDIR=/sources/stage/vim install
ln -s vim /sources/stage/vim/usr/bin/vi
for page in /sources/stage/vim/usr/share/man/{,*/}man1/vim.1; do
 test -f "$page" || continue
 ln -s vim.1 "$(dirname "$page")/vi.1"
done
mkdir -p /sources/stage/vim/usr/share/doc/vim /sources/stage/vim/etc
ln -s ../vim/vim92/doc /sources/stage/vim/usr/share/doc/vim-9.2.1201
cp LICENSE /sources/stage/vim/usr/share/doc/vim/copyright
cat > /sources/stage/vim/etc/vimrc <<'VIMRC'
" Ensure defaults precede local customization.
source $VIMRUNTIME/defaults.vim
let skip_defaults_vim=1
set nocompatible
set backspace=2
set mouse=
syntax on
if (&term == "xterm") || (&term == "putty")
  set background=dark
endif
VIMRC

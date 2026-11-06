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
su tester -c 'PATH=/sources/test-inputs/vim-glvs/bin:$PATH LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8 TERM=xterm-256color make -j1 test' \
 < /dev/null > /sources/evidence/h07-vim/check.log 2>&1
grep -E 'FAILED:[[:space:]]+0' /sources/evidence/h07-vim/check.log
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

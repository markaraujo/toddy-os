#!/bin/bash
# Frozen LFS 13.1-systemd chapter 8: ninja; staged install.
set -euo pipefail
cd /sources/ninja-1.13.2
test ! -e /sources/stage/ninja
export NINJAJOBS=8
sed -i '/int Guess/a \
  int   j = 0;\
  char* jobs = getenv( "NINJAJOBS" );\
  if ( jobs != NULL ) j = atoi( jobs );\
  if ( j > 0 ) return j;\
' src/ninja.cc

python3 configure.py --bootstrap --verbose

install -d /sources/stage/ninja/usr/bin
install -vm755 ninja /sources/stage/ninja/usr/bin/
install -vDm644 misc/bash-completion /sources/stage/ninja/usr/share/bash-completion/completions/ninja
install -vDm644 misc/zsh-completion  /sources/stage/ninja/usr/share/zsh/site-functions/_ninja
mkdir -p /sources/stage/ninja/usr/share/doc/ninja
cp COPYING /sources/stage/ninja/usr/share/doc/ninja/copyright

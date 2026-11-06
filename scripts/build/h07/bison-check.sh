#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $(dpkg-query --admindir="$LFS/var/lib/dpkg" -W -f='${Status}' bison) == 'install ok installed' ]]
check_native /usr/bin/bison 3.8.2
chroot_run <<'INNER'
set -euo pipefail
cat > /tmp/toddy-parser.y <<'Y'
%{ int yylex(void); void yyerror(const char *); %}
%%
start: ;
%%
int yylex(void) { return 0; }
void yyerror(const char *s) { (void)s; }
int main(void) { return yyparse(); }
Y
bison -o /tmp/toddy-parser.c /tmp/toddy-parser.y
gcc /tmp/toddy-parser.c -o /tmp/toddy-parser
/tmp/toddy-parser
rm /tmp/toddy-parser{,.c,.y}
INNER

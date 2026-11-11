#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile ]]
export PYTHONDONTWRITEBYTECODE=1
ulimit -c 0
cp -a /src /build/compile
cd /build/compile
perl Makefile.PL INSTALLDIRS=vendor NO_PERLLOCAL=1 NO_PACKLIST=1 > /build/configure.log 2>&1
make -j4 > /build/original-build.log 2>&1
timeout 90 make test > /build/original-tests.log 2>&1
make DESTDIR=/stage install > /build/original-stage.log 2>&1

vendorlib=$(perl -MConfig -e 'print $Config{vendorlib}')
export PERL5LIB="/stage$vendorlib"
mkdir /build/probe
cd /build/probe
cat > fixture.yp <<'GRAMMAR'
%token NUMBER
%%
input: NUMBER '+' NUMBER { $_[1] + $_[3] };
%%
GRAMMAR
/stage/usr/bin/yapp -m ToddyFixture -o ToddyFixture.pm fixture.yp > /build/local-generator.log 2>&1
perl -I. -MToddyFixture -MParse::Yapp -e '
    use strict;
    use warnings;
    die "wrong version" unless $Parse::Yapp::VERSION eq "1.21";
    for (1..2) {
        my @bad = (["NUMBER", 1], ["+", "+"], ["+", "+"]);
        my $rejected = !eval {
            ToddyFixture->new->YYParse(yylex => sub { @{shift(@bad) // ["", undef]} },
                                       yyerror => sub { die "syntax-refused" });
            1;
        };
        die "invalid input accepted" unless $rejected && $@ =~ /^syntax-refused/;
        my @good = (["NUMBER", 19], ["+", "+"], ["NUMBER", 23]);
        my $value = ToddyFixture->new->YYParse(yylex => sub { @{shift(@good) // ["", undef]} },
                                               yyerror => sub { die "valid input refused" });
        die "wrong value" unless $value == 42;
    }
    print "Parse::Yapp generated parser refused invalid input and recovered twice\n";
' > /build/local-probe.log

python3 - <<'PYTEST'
import hashlib
import json
import os
from pathlib import Path
import re

work = Path('/build')
stage = Path('/stage')
tests = (work / 'original-tests.log').read_text()
totals = re.search(r'Files=(\d+), Tests=(\d+)', tests)
assert totals and int(totals[1]) == 3 and int(totals[2]) > 10
assert 'All tests successful.' in tests and 'Result: PASS' in tests
consumer = (work / 'local-probe.log').read_text()
assert consumer == 'Parse::Yapp generated parser refused invalid input and recovered twice\n'
payload = {str(p.relative_to(stage)): hashlib.sha256(p.read_bytes()).hexdigest()
           for p in stage.rglob('*') if p.is_file() and not p.is_symlink()}
assert 'usr/bin/yapp' in payload and any(p.endswith('/Parse/Yapp.pm') for p in payload)
assert not any(p.endswith(('/.packlist', '/perllocal.pod')) for p in payload)
space = os.statvfs(work)
assert space.f_bavail * space.f_frsize >= 16 * 1024**3
result = {'version': '1.21', 'compile_exit': 0, 'stage_exit': 0, 'upstream_programs': int(totals[1]),
          'upstream_cases': int(totals[2]), 'consumer': consumer, 'stage_sha256': payload}
(work / 'stage-results.json').write_text(json.dumps(result, indent=2) + '\n')
PYTEST

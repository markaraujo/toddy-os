#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
PYTHONDONTWRITEBYTECODE=1 python3 - "$1" <<'PYTEST'
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

target = Path('/mnt/lfs')
root = Path('/opt/toddy-build')
sys.path.insert(0, str(root / 'scripts/build/phase2'))
from qualify_samba_build_tools import digest, qualify

name = sys.argv[1]
version = {'rpcsvc-proto': '1.4.4', 'perl-parse-yapp': '1.21'}[name]
entries = qualify(root, name)
chroot = ['chroot', str(target)]
env = {'PATH': '/usr/bin:/usr/sbin', 'LC_ALL': 'C.UTF-8'}
status = subprocess.check_output(chroot + ['dpkg-query', '-W', '-f=${Status} ${Version}', name], text=True)
assert status == 'install ok installed ' + version + '-1+toddy1'
assert not subprocess.check_output(chroot + ['dpkg', '--audit'], text=True).strip()
subprocess.run(chroot + ['apt-get', 'check'], check=True)
for path, row in entries.items():
    if 'sha256' in row:
        assert digest(target / path) == row['sha256']
    elif 'symlink' in row:
        assert (target / path).readlink() == Path(row['symlink'])
docs = target / 'usr/share/doc' / name
notices = json.loads((docs / 'source-notices/index.json').read_text())['sources'][0]['notices']
expected = {'COPYING'} if name == 'rpcsvc-proto' else {'README', 'Yapp.pm'}
assert expected <= {Path(row['path']).name for row in notices}
assert all(digest(docs / 'source-notices' / row['sha256']) == row['sha256'] for row in notices)

with tempfile.TemporaryDirectory(prefix='toddy-samba-tool-', dir=target / 'tmp') as directory:
    tmp = Path(directory)
    os.chown(tmp, 101, 101)
    env['HOME'] = '/tmp/' + tmp.name
    wrapper = '''
set -euo pipefail
mount --make-rprivate /
mount -t tmpfs -o size=1m,nosuid,nodev tmpfs /mnt/lfs/dev
for name in null zero random urandom; do
    touch "/mnt/lfs/dev/$name"
    mount --bind "/dev/$name" "/mnt/lfs/dev/$name"
done
mount -t proc -o nosuid,nodev,noexec proc /mnt/lfs/proc
exec chroot --userspec=101:101 /mnt/lfs "$@"
'''
    launch = '''
import ctypes, os, sys
assert os.geteuid() == os.getegid() == 101
assert ctypes.CDLL(None, use_errno=True).prctl(38, 1, 0, 0, 0) == 0
status = open('/proc/self/status').read()
assert 'CapEff:\\t0000000000000000' in status and 'NoNewPrivs:\\t1' in status
os.chdir(os.environ['HOME'])
os.execv(sys.argv[1], sys.argv[1:])
'''
    base = ['unshare', '--mount', '--pid', '--fork', '--net', 'bash', '-c', wrapper,
            'toddy-samba-tool', 'python3', '-c', launch]

    def execute(*args):
        return subprocess.check_output(base + list(args), env=env, text=True, timeout=30)

    if name == 'rpcsvc-proto':
        shutil.copyfile(root / 'scripts/build/phase2/rpcsvc-proto-probe.c', tmp / 'probe.c')
        (tmp / 'fixture.x').write_text('struct fixture { unsigned int sequence; string label<12>; };\n')
        (tmp / 'invalid.x').write_text('struct fixture { @ };\n')
        invalid = subprocess.run(base + ['/usr/bin/rpcgen', '-C', '-h', '-o', 'invalid.h', 'invalid.x'],
                                 env=env, capture_output=True, timeout=15)
        assert invalid.returncode > 0 and invalid.stderr
        execute('/usr/bin/rpcgen', '-C', '-h', '-o', 'fixture.h', 'fixture.x')
        execute('/usr/bin/rpcgen', '-C', '-c', '-o', 'fixture_xdr.c', 'fixture.x')
        execute('/usr/bin/cc', '-I/usr/include/tirpc', '-Werror=implicit-function-declaration',
                'fixture_xdr.c', 'probe.c', '-ltirpc', '-o', 'consumer')
        actual = execute(env['HOME'] + '/consumer').strip()
        assert actual == 'Generated rpcgen XDR C round-tripped two records'
    else:
        (tmp / 'fixture.yp').write_text("%token NUMBER\n%%\ninput: NUMBER '+' NUMBER { $_[1] + $_[3] };\n%%\n")
        execute('/usr/bin/yapp', '-m', 'ToddyFixture', '-o', 'ToddyFixture.pm', 'fixture.yp')
        actual = execute('/usr/bin/perl', '-I.', '-MToddyFixture', '-MParse::Yapp', '-e', '''
use strict;
use warnings;
die unless $Parse::Yapp::VERSION eq "1.21";
die unless $INC{"Parse/Yapp.pm"} eq "/usr/lib/perl5/5.44/vendor_perl/Parse/Yapp.pm";
for (1..2) {
    my @bad = (["NUMBER", 1], ["+", "+"], ["+", "+"]);
    my $accepted = eval {
        ToddyFixture->new->YYParse(yylex => sub { @{shift(@bad) // ["", undef]} },
                                   yyerror => sub { die "syntax-refused" });
        1;
    };
    die unless !$accepted && $@ =~ /^syntax-refused/;
    my @good = (["NUMBER", 19], ["+", "+"], ["NUMBER", 23]);
    die unless ToddyFixture->new->YYParse(yylex => sub { @{shift(@good) // ["", undef]} },
                                          yyerror => sub { die "valid input refused" }) == 42;
}
print "Parse::Yapp generated parser refused invalid input and recovered twice\n";
''').strip()
        assert actual == 'Parse::Yapp generated parser refused invalid input and recovered twice'

space = os.statvfs(target)
assert space.f_bavail * space.f_frsize >= 16 * 1024**3
proof = {'consumer': actual, 'notices_verified': len(notices),
         'scope': 'Installed build tool under UID101 and NNP, private devices and network. Local generated parser only.',
         'physical_machine_tested': False}
Path('/var/log/toddy/phase2', name + '-installed-consumer.json').write_text(json.dumps(proof, indent=2) + '\n')
PYTEST

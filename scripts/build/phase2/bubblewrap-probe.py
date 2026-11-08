"""Actual nested user/mount/PID/network namespaces, read-only usr and no outer work."""
import json
import os
from pathlib import Path
import subprocess
import sys

bwrap = sys.argv[1]
assert Path(bwrap).is_file()
probe = '''import os,pathlib
assert os.getuid()==101 and os.getpid()==1, (os.getuid(),os.getpid())
assert all(not pathlib.Path(p).exists() for p in ['/src','/build','/stage'])
p=pathlib.Path('/tmp/private');p.write_text('navy');assert p.read_text()=='navy'
try:
 pathlib.Path('/usr/toddy-write-refused').write_text('no')
except OSError as e:
 assert e.errno==30
else:
 raise AssertionError('read-only usr writable')
status=pathlib.Path('/proc/self/status').read_text()
assert 'NoNewPrivs:\\t1' in status
interfaces={line.split(':',1)[0].strip() for line in pathlib.Path('/proc/net/dev').read_text().splitlines()[2:]}
assert interfaces <= {'lo'}
print('private namespaces/read-only usr/no outer work/writable tmp verified')
'''
command = [bwrap,'--unshare-all','--as-pid-1','--die-with-parent','--new-session',
           '--ro-bind','/usr','/usr','--ro-bind','/lib64','/lib64',
           '--symlink','usr/bin','/bin','--symlink','usr/lib','/lib',
           '--proc','/proc','--dev','/dev','--tmpfs','/tmp',
           '/usr/bin/python3','-B','-c',probe]
r = subprocess.run(command, capture_output=True, text=True)
print(r.stdout, end='');print(r.stderr, end='', file=sys.stderr)
assert r.returncode==0, r.returncode
print(json.dumps({'native_namespace_exit':0,'outer_work_hidden':True,'readonly_usr':True,'private_tmp':True,'no_new_privileges':True}))

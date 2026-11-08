#!/usr/bin/env python3
"""Synthetic proof only: observe bounded public toy-package output privately."""
import os
from pathlib import Path
import native_backends
import service

assert os.getuid()==0
expected='deb [signed-by=/build/package-proof/repository.gpg] file:/build/package-proof/repo ./\n'
assert Path('/etc/apt/sources.list').read_text()==expected
assert not list(Path('/etc/apt/sources.list.d').iterdir())
original=native_backends.run_command

def observed(args,*positional,**keywords):
    result=original(args,*positional,**keywords)
    if args['argv'][0]=='/usr/bin/apt-get':
        with Path('/build/package-proof/transaction-private.log').open('ab') as output:
            os.chmod(output.name,0o600)
            output.write(result.get('_private_output',b''))
            output.write(b'\nEXIT '+str(result['exit']).encode()+b'\n')
    return result

native_backends.run_command=observed
service.main()

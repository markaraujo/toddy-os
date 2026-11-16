#!/usr/bin/python3 -I
"""Fixed Polkit-authenticated owner surface; never a model-facing grant method.

Install root-owned and nonwritable at /usr/lib/toddy/executor/owner_policy.py.
Invoke that exact executable with pkexec; Python isolated mode excludes caller
modules/environment. Caller UID comes only from pkexec, not CLI/profile JSON.
"""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

# Isolated-mode script invocation intentionally does not add the script directory.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from store import Store, PolicyError, owner


def caller_uid():
    if os.getuid() != 0 or os.geteuid() != 0:
        raise PolicyError('owner_authentication_required')
    raw = os.environ.get('PKEXEC_UID', '')
    if not re.fullmatch(r'[1-9][0-9]{0,9}', raw):
        raise PolicyError('authenticated_caller_required')
    return owner(int(raw))


def active_session(uid):
    # logind, not a caller-supplied session string, selects the display session.
    r = subprocess.run(['/usr/bin/loginctl', 'show-user', str(uid), '-p', 'Display', '--value'],
                       capture_output=True, text=True, timeout=5, check=True,
                       env={'PATH': '/usr/bin:/usr/sbin', 'LC_ALL': 'C.UTF-8'})
    session = r.stdout.strip()
    if not re.fullmatch(r'[a-zA-Z0-9_-]{1,128}', session):
        raise PolicyError('active_owner_session_required')
    r = subprocess.run(['/usr/bin/loginctl', 'show-session', session,
                        '-p', 'User', '-p', 'Active', '-p', 'Remote'],
                       capture_output=True, text=True, timeout=5, check=True,
                       env={'PATH': '/usr/bin:/usr/sbin', 'LC_ALL': 'C.UTF-8'})
    values = dict(line.split('=', 1) for line in r.stdout.splitlines())
    if values != {'User': str(uid), 'Active': 'yes', 'Remote': 'no'}:
        raise PolicyError('active_owner_session_required')
    return session


def main():
    p = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    p.add_argument('action', choices=['grant', 'revoke', 'audit'])
    p.add_argument('--mode', choices=['session', 'standing'])
    p.add_argument('--expires-in', type=int)
    args = p.parse_args()
    os.umask(0o077)
    try:
        uid = caller_uid()
        if args.action == 'grant':
            if args.mode is None or args.expires_in is None or not 1 <= args.expires_in <= 365 * 86400:
                raise PolicyError('invalid_grant')
            session = active_session(uid) if args.mode == 'session' else None
            store = Store(Path('/var/lib/toddy/executor'))
            generation = store.set_grant(uid, args.mode, expires=time.time() + args.expires_in, session=session)
            result = {'state': 'granted', 'uid': uid, 'generation': generation,
                      'scope': 'full administration; arbitrary effects may be irreversible'}
        else:
            if args.mode is not None or args.expires_in is not None:
                raise PolicyError('invalid_policy_arguments')
            store = Store(Path('/var/lib/toddy/executor'))
            result = ({'state': 'revoked', 'uid': uid, 'generation': store.revoke(uid)}
                      if args.action == 'revoke' else {'uid': uid, 'audit': store.audit(uid)})
        print(json.dumps(result))
    except (PolicyError, OSError, ValueError, subprocess.SubprocessError) as error:
        code = str(error) if isinstance(error, PolicyError) else 'owner_policy_failed'
        print(json.dumps({'state': 'error', 'code': code}))
        raise SystemExit(1)


if __name__ == '__main__':
    main()

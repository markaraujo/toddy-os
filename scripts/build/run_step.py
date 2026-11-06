#!/usr/bin/env python3
"""Run one guarded guest recipe with durable logs, exit code and file manifest.

Always run as guest root; --user selects root or the unprivileged lfs user.
A success record requires recipe AND postcondition exit zero. Never infer it
from log text. Interrupted running.json is unfinished, not a success marker.
"""
import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
TARGET = Path('/mnt/lfs')
STATE = Path('/var/log/toddy/build')


def recipe_command(user):
    # Detached launchers may inherit SIGINT/SIGQUIT ignored from a shell.
    # A new session alone does not reset ignored dispositions across exec.
    command = ['env', '--default-signal=HUP,INT,QUIT,TERM',
               'bash', '--noprofile', '--norc', '-c',
               ('source /home/lfs/.bashrc; ' if user == 'lfs' else '') + 'exec bash "$1"',
               'recipe']
    if user == 'lfs':
        command = ['/usr/sbin/runuser', '-u', 'lfs', '--'] + command
    return command


def snapshot():
    result = {}
    for tree in ('usr', 'etc', 'var', 'tools', 'lib64'):
        for base, dirs, files in os.walk(TARGET / tree, followlinks=False):
            for name in dirs + files:
                path = Path(base) / name
                stat = path.lstat()
                item = {'mode': stat.st_mode, 'uid': stat.st_uid, 'gid': stat.st_gid}
                if path.is_symlink():
                    item['link'] = os.readlink(path)
                elif path.is_file():
                    with path.open('rb') as stream:
                        item['sha256'] = hashlib.file_digest(stream, 'sha256').hexdigest()
                result['/' + str(path.relative_to(TARGET))] = item
    return result


def write(path, data):
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(data, indent=2) + '\n')
    temp.replace(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('step')
    parser.add_argument('recipe', type=Path)
    parser.add_argument('postcheck', type=Path)
    parser.add_argument('--user', choices=['root', 'lfs'], default='lfs')
    args = parser.parse_args()
    if not args.step.replace('-', '').replace('_', '').isalnum():
        raise SystemExit('Unsafe step id')
    if os.geteuid() != 0:
        raise SystemExit('Dispatcher requires disposable-guest root')
    # Execute the same target identity/mount guard before any target traversal.
    subprocess.run(['bash', '-c', 'source "$1"; guard_target', 'guard',
                    str(HERE / 'target.sh')], check=True)
    for path in (args.recipe, args.postcheck):
        if not path.resolve().is_relative_to(HERE.parent.parent):
            raise SystemExit('Recipe/postcheck outside project build scripts')
        if not path.is_file():
            raise SystemExit(f'Missing recipe/postcondition: {path}')
    STATE.mkdir(parents=True, exist_ok=True)
    with (STATE / 'build.lock').open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        prefix = STATE / args.step
        if prefix.with_suffix('.success.json').exists():
            raise SystemExit('Step already passed; inspect checkpoint before intentional rebuild')
        if prefix.with_suffix('.running.json').exists():
            raise SystemExit('Interrupted step detected; inspect partial installation before retry')
        if prefix.with_suffix('.failed.json').exists():
            history = STATE / 'history' / (args.step + '-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f'))
            history.mkdir(parents=True)
            for suffix in ('.failed.json', '.manifest.json', '.log'):
                previous = prefix.with_suffix(suffix)
                if previous.exists():
                    previous.replace(history / previous.name)
        before = snapshot()
        record = {'step': args.step, 'started': datetime.now(timezone.utc).isoformat(),
                  'recipe_sha256': hashlib.sha256(args.recipe.read_bytes()).hexdigest(),
                  'postcheck_sha256': hashlib.sha256(args.postcheck.read_bytes()).hexdigest(),
                  'user': args.user,
                  'runner_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  'source_lock_sha256': hashlib.sha256((HERE.parents[1] / 'config/sources.lock.json').read_bytes()).hexdigest(),
                  'book_lock_sha256': hashlib.sha256((HERE.parents[1] / 'config/books.lock.json').read_bytes()).hexdigest()}

        overlay = HERE.parents[1] / 'config/security-overlay.lock.json'
        if overlay.exists():
            record['security_overlay_sha256'] = hashlib.sha256(overlay.read_bytes()).hexdigest()
        write(prefix.with_suffix('.running.json'), record)
        environment = {'HOME': '/home/lfs' if args.user == 'lfs' else '/root',
                       'TERM': 'dumb',
                       'PATH': '/usr/bin:/bin' if args.user == 'lfs' else '/usr/bin:/usr/sbin:/bin:/sbin',
                       'LC_ALL': 'POSIX'}
        command = recipe_command(args.user)
        with prefix.with_suffix('.log').open('a') as log:
            process = subprocess.Popen(command + [str(args.recipe.resolve())],
                env=environment, stdout=log, stderr=subprocess.STDOUT,
                cwd='/mnt/lfs/sources', start_new_session=True)
            record['recipe_pid'] = process.pid
            record['recipe_pgid'] = process.pid
            write(prefix.with_suffix('.running.json'), record)
            record['recipe_exit'] = process.wait()
            record['postcheck_exit'] = None
            if record['recipe_exit'] == 0:
                check = subprocess.run(command + [str(args.postcheck.resolve())],
                    env=environment, stdout=log, stderr=subprocess.STDOUT, cwd='/mnt/lfs/sources')
                record['postcheck_exit'] = check.returncode
        after = snapshot()
        changes = {name: {'before': before.get(name), 'after': after.get(name)}
                   for name in sorted(before.keys() | after.keys()) if before.get(name) != after.get(name)}
        write(prefix.with_suffix('.manifest.json'), changes)
        record['finished'] = datetime.now(timezone.utc).isoformat()
        record['changed_paths'] = len(changes)
        record['log_sha256'] = hashlib.sha256(prefix.with_suffix('.log').read_bytes()).hexdigest()
        success = record['recipe_exit'] == 0 and record['postcheck_exit'] == 0
        write(prefix.with_suffix('.success.json' if success else '.failed.json'), record)
        prefix.with_suffix('.running.json').unlink()
        print(json.dumps(record))
        if not success:
            raise SystemExit(1)


if __name__ == '__main__':
    main()

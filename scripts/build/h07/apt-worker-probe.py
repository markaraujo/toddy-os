#!/usr/bin/env python3
"""Run a real acquisition command and observe its native worker credentials."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import pwd
import signal
import subprocess
import time


def process_stat(pid):
    fields = Path('/proc', str(pid), 'stat').read_text().rsplit(') ', 1)[1].split()
    return int(fields[1]), int(fields[19])  # PPid and kernel start time


def descendants(parent):
    parents = {}
    for entry in Path('/proc').iterdir():
        if not entry.name.isdigit():
            continue
        try:
            parents[int(entry.name)] = process_stat(int(entry.name))[0]
        except (FileNotFoundError, ProcessLookupError):
            continue
    selected, pending = set(), [parent]
    while pending:
        current = pending.pop()
        children = {pid for pid, ppid in parents.items() if ppid == current} - selected
        selected.update(children)
        pending.extend(children)
    return selected


def worker_state(pid, executable):
    before = process_stat(pid)
    path = Path('/proc', str(pid))
    if (path / 'exe').resolve(strict=True) != executable:
        return None
    fields = dict(line.split(':', 1) for line in (path / 'status').read_text().splitlines())
    state = {'pid': pid, 'start_time': before[1],
             'uids': [int(value) for value in fields['Uid'].split()],
             'gids': [int(value) for value in fields['Gid'].split()],
             'groups': [int(value) for value in fields['Groups'].split()],
             'effective_capabilities': int(fields['CapEff'].strip(), 16),
             'no_new_privileges': int(fields['NoNewPrivs'].strip()),
             'seccomp_mode': int(fields['Seccomp'].strip()),
             'seccomp_filters': int(fields['Seccomp_filters'].strip())}
    if process_stat(pid) != before:
        return None
    return state


def sandboxed(state, uid, gid, inherited_filters):
    return (uid != 0 and gid != 0 and state['uids'] == [uid] * 4 and
            state['gids'] == [gid] * 4 and set(state['groups']) <= {gid} and
            state['effective_capabilities'] == 0 and state['no_new_privileges'] == 1 and
            state['seccomp_mode'] == 2 and state['seccomp_filters'] > inherited_filters)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--user', required=True)
    parser.add_argument('--executable', type=Path, required=True)
    parser.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ['--'] else args.command
    if os.geteuid() != 0 or not command:
        raise SystemExit('Requires disposable-target root and a real command')
    identity = pwd.getpwnam(args.user)
    if identity.pw_uid == 0 or identity.pw_gid == 0:
        raise SystemExit('Expected worker identity must be unprivileged')
    executable = args.executable.resolve(strict=True)
    own_status = dict(line.split(':', 1) for line in Path('/proc/self/status').read_text().splitlines())
    inherited_filters = int(own_status['Seccomp_filters'].strip())
    # Open before spawning: never overwrite an earlier acceptance observation.
    with args.output.open('x') as stream:
        os.fchmod(stream.fileno(), 0o600)
        record = {'started': datetime.now(timezone.utc).isoformat(),
                  'expected_executable': str(executable), 'uid': identity.pw_uid,
                  'gid': identity.pw_gid, 'inherited_seccomp_filters': inherited_filters,
                  'states': [], 'accepted': False}
        seen = set()
        process = subprocess.Popen(command, start_new_session=True)
        record['command_pid'] = process.pid
        try:
            while process.poll() is None:
                for pid in descendants(process.pid):
                    try:
                        state = worker_state(pid, executable)
                    except (FileNotFoundError, ProcessLookupError):
                        continue
                    if state is None:
                        continue
                    key = json.dumps(state, sort_keys=True)
                    if key not in seen:
                        seen.add(key)
                        record['states'].append(state)
                time.sleep(0.02)
            record['command_exit'] = process.wait()
            record['sandboxed_workers'] = sorted({state['pid'] for state in record['states']
                if sandboxed(state, identity.pw_uid, identity.pw_gid, inherited_filters)})
            record['accepted'] = record['command_exit'] == 0 and bool(record['sandboxed_workers'])
        except BaseException as error:
            record['error'] = str(error)
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            try:
                record['command_exit'] = process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                record['command_exit'] = process.wait()
            raise
        finally:
            record['finished'] = datetime.now(timezone.utc).isoformat()
            json.dump(record, stream, indent=2)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
    if not record['accepted']:
        raise SystemExit('Real acquisition failed or no fully sandboxed worker was observed')
    print('NATIVE_SANDBOXED_WORKER_OBSERVED effective IDs/groups, zero capabilities, no_new_privs, seccomp filter')


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Read-only, source-qualified Berkeley DB standard-suite progress.

TestNNN names repeat in several groups. Only the outer run_std output identifies
the current group. Reaching a later group does not mean earlier tests passed.
"""
import hashlib
import re
from collections import deque
from pathlib import Path

SOURCE_SHA256 = '81b82f33c9ca4fc878ee51fd1f235645824f1d4faba28d187bc23955c21681df'
CONFIG_SHA256 = '12a33fcd1ac46b1296fd1916e6a1cb588dc35432d93adffea661188b0e07e941'
# Frozen db-5.3.28 test/tcl/test.tcl run_std, with the verified native build's
# HAVE_CRYPTO/HAVE_QUEUE/HAVE_HASH/HAVE_HEAP. Do not silently generalize it.
GROUPS = ['environment', 'archive', 'backup', 'file operations', 'locking',
          'logging', 'memory pool', 'mutex', 'transaction', 'deadlock detection',
          'subdatabase', 'byte-order', 'recno backing file', 'DBM interface',
          'NDBM interface', 'Hsearch interface', 'secondary index', 'partition',
          'compression', 'automated repmgr tests', 'other repmgr tests',
          'repmgr multi-process', 'replication', 'security', 'recovery', 'join',
          'access-method matrix']
METHODS = ['btree', 'rbtree', 'recno', 'frecno', 'rrecno', 'queue', 'queueext', 'hash', 'heap']
HEADERS = (['Running ' + group + ' tests' for group in GROUPS[:25]]
           + ['Running join test'] + ['Running ' + method + ' tests' for method in METHODS])


def classify(outer_log):
    headers = [line for line in outer_log.splitlines() if line.startswith('Running ')]
    if not headers:
        raise ValueError('No outer run_std group header; progress is unknown')
    if headers != HEADERS[:len(headers)]:
        raise ValueError('Unexpected, repeated or out-of-order outer group headers; progress is unknown')
    group_index = min(len(headers) - 1, 26)
    method_index = len(headers) - 27 if len(headers) > 26 else None
    return {'group_number': group_index + 1, 'group_count': len(GROUPS),
            'group': GROUPS[group_index], 'outer_header': headers[-1],
            'outer_headers_started': len(headers), 'outer_header_count': len(HEADERS),
            'groups_returned_before_current': group_index,
            'returned_groups_are_not_pass_claims': True,
            'remaining_after_current': GROUPS[group_index + 1:],
            'access_method': METHODS[method_index] if method_index is not None else None,
            'access_method_number': method_index + 1 if method_index is not None else None,
            'access_method_count': len(METHODS), 'time_percent_estimated': False}


def observe(source, outer_path, all_out):
    source = Path(source)
    for path, expected in ((source / 'test/tcl/test.tcl', SOURCE_SHA256),
                           (source / 'build-test/db_config.h', CONFIG_SHA256)):
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError('Suite source/configuration differs from the reviewed progress plan')
    before = Path(outer_path).read_text(errors='replace')
    last = configuration = dispatch = None
    failures = []
    tail = deque(maxlen=5)
    with Path(all_out).open(errors='replace') as stream:
        for line in stream:
            line = line.rstrip('\n')
            tail.append(line)
            if re.match(r'^\s*[A-Z][A-Za-z_]*\d{3}[.: ]', line):
                last = line.strip()
            if re.match(r'^(?:Recd|Fop|Test)[0-9]{3}[: (]', line):
                configuration = line
            if line.startswith('eval { test'):
                dispatch = line
            if line.startswith('FAIL'):
                failures.append(line)
    after = Path(outer_path).read_text(errors='replace')
    progress = classify(after)
    progress['group_transition_during_observation'] = classify(before)['outer_header'] != progress['outer_header']
    return {'progress': progress, 'outer_log': str(outer_path),
            'outer_log_sha256': hashlib.sha256(after.encode()).hexdigest(),
            'outer_log_snapshot': after, 'suite_source_sha256': SOURCE_SHA256,
            'suite_config_sha256': CONFIG_SHA256, 'last_case': last,
            'configuration': configuration, 'last_dispatch': dispatch,
            'tail': list(tail), 'failures': failures}

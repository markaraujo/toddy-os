#!/usr/bin/env python3
"""Accept only the observed, source-qualified getcap formatting difference."""
import json
from pathlib import Path
import re
import sys


def evaluate(output, detail, raw_exit):
    results={}
    for match in re.finditer(r'^[ \t]*(\d+): [^\n]+?[ \t]+(ok|skipped|FAILED)(?:[ \t].*)?$',output,re.M):
        number=int(match[1])
        if number in results:
            raise ValueError('Duplicate Tar group')
        results[number]=match[2]
    if set(results)!=set(range(1,245)):
        raise ValueError('Incomplete Tar suite')
    failed=[n for n,result in results.items() if result=='FAILED']
    skipped=sum(result=='skipped' for result in results.values())
    if raw_exit==0:
        if failed or f'All {244-skipped} tests were successful.' not in output:
            raise ValueError('Inconsistent successful Tar suite')
    elif raw_exit==2:
        if failed!=[233] or skipped!=20 or 'ERROR: 224 tests were run,\n1 failed unexpectedly.\n20 tests were skipped.' not in output:
            raise ValueError('Unknown Tar failure/summary')
        changes=[line for line in detail.splitlines() if line.startswith(('+','-')) and not line.startswith(('+++','---'))]
        if changes!=['-dir/file = cap_chown=ei','+dir/file cap_chown=ei']:
            raise ValueError('Unknown capability regression')
        if 'FAILED (capabs_raw01.at:28)' not in detail:
            raise ValueError('Missing expected failure location')
    else:
        raise ValueError('Unexpected raw make exit')
    return {'groups':244,'pass':244-skipped-len(failed),'skip':skipped,
            'known_format_failures':failed,'raw_make_exit':raw_exit,
            'all_pass':not failed,'native_capability_roundtrip_required':True}

if __name__=='__main__':
    base=Path(sys.argv[1])
    result=evaluate((base/'check.log').read_text(),
                    (base/'capability-test.log').read_text() if (base/'capability-test.log').exists() else '',
                    int((base/'check.exit').read_text()))
    (base/'classification.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))

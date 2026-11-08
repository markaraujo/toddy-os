#!/usr/bin/env python3
"""Measure the unchanged full-root runner for Phase2; no optimized-path bypass."""
import json
import os
from pathlib import Path
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import run_step

if __name__=='__main__':
    step=sys.argv[1]
    assert step.replace('-','').replace('_','').isalnum()
    original=run_step.snapshot
    report={'step':step,'scope':'same full-root snapshot function, timing only','snapshots':[]}
    destination=Path('/var/log/toddy/phase2')/(step+'-timing.json')
    assert not destination.exists(),'Reconcile prior measured dispatch; no replay'
    started=time.monotonic()
    def measured():
        began=time.monotonic();result=original();elapsed=time.monotonic()-began
        files=[name for name,value in result.items() if 'sha256' in value]
        report['snapshots'].append({'seconds':round(elapsed,3),'entries':len(result),'regular_files':len(files),
            'regular_bytes':sum((run_step.TARGET/name.lstrip('/')).stat().st_size for name in files)})
        return result
    run_step.snapshot=measured
    try:run_step.main()
    finally:
        report['total_seconds']=round(time.monotonic()-started,3)
        part=destination.with_suffix('.part');part.write_text(json.dumps(report,indent=2)+'\n');part.replace(destination)

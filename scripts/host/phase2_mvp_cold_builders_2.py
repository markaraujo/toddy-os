#!/usr/bin/env python3
"""Second fixed inactive-builder pair; reuse exact opaque custody protocol."""
import hashlib,importlib.util,json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import phase2_compress_cold_checkpoints as cold
SOURCE=HERE/'phase2_mvp_cold_builders.py'
SOURCE_SHA256='715af337c5415a33b6c2f3bf923272fbe4fed7edfa1bf45cd0e1bbf68060c1d6'
if SOURCE.resolve()!=SOURCE or hashlib.sha256(SOURCE.read_bytes()).hexdigest()!=SOURCE_SHA256:raise ValueError('Reviewed shared cold-builder guard changed')
spec=importlib.util.spec_from_file_location('_toddy_cold_builder_guard_2',SOURCE)
_guard=importlib.util.module_from_spec(spec);spec.loader.exec_module(_guard)
PROFILES={
 'h07-final-base-builder.qcow2':{'manifest':'h07-final-base.json','manifest_sha256':'8bc7d4f035e2a3971ac063c0b0d1425fab20d84a65fa694ffeb35354d797bbf9',
  'sha256':'a19c5c75dda427a45fffdb33bfbd66f7f5c753ba18abd3dd37a0adf8bf7fb154','device':66306,'inode':11833468,'bytes':6496976896,'allocated':6478241792,'mtime_ns':1794051806355006514,'ctime_ns':1794051806355006514},
 'h09-boot-ready-builder.qcow2':{'manifest':'h09-boot-ready.json','manifest_sha256':'db07aba2b3778ae6a4cfdfccd5d49f9b1ef63f238a27b09d2a50f7c2dfa420bc',
  'sha256':'8ca06a77eafbd0d7def51bce9a35c470bb8ad1bc4bb66f506ce8fda097f4f316','device':66306,'inode':11835845,'bytes':6497894400,'allocated':6479187968,'mtime_ns':1794052904679800038,'ctime_ns':1794052904679800038}}
# Private module instance: the original pair and context cannot be rebound.
_guard.PROFILES=PROFILES
ROOT=_guard.ROOT
manifest=_guard.manifest
image_identity=_guard.image_identity
graph=_guard.graph
inspect=_guard.inspect

if __name__=='__main__':
 if sys.argv[1:]==['inspect']:print(json.dumps(inspect(),sort_keys=True))
 elif sys.argv[1:]==['compress']:
  sys.argv=[sys.argv[0],'--profile','mvp-builders-2'];cold.main()
 else:raise SystemExit('Only fixed inspect|compress actions; no path arguments')

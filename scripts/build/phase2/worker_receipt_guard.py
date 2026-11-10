"""Keep private-worker preparation receipts out of native build acceptance paths."""
from pathlib import Path

def validate(path,component):
 if component not in {'cups','mitkrb','libgtop','modemmanager'}:
  raise ValueError('Unknown private-worker receipt owner')
 expected=Path('/var/log/toddy/phase2')/(component+'-shared-scratch-1.json')
 if path!=expected:
  raise ValueError('Private-worker receipt cannot replace native or another worker evidence')

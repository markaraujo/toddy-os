#!/usr/bin/env python3
"""Fixed native export5 public signature entry, exact known stream contract."""
import sys
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parent))
from export4_public_signatures import main
if __name__=='__main__':
    if Path(__file__).resolve()!=Path('/opt/toddy-build/scripts/build/phase2/export5_public_signatures.py'):raise ValueError('Fixed root export5 entry required')
    main(5)

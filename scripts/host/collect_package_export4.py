#!/usr/bin/env python3
"""Fixed readonly unsigned export4 transfer; preserve exports2/3."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from collect_package_export2 import transfer
if __name__=='__main__':
    if sys.argv[1:]:raise SystemExit('No arbitrary source/destination/action arguments')
    transfer(4)

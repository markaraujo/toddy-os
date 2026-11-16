#!/usr/bin/env python3
"""Only fresh export5 public signatures; no earlier intent or signing context."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from stage_package_export4_signatures import main
if __name__=='__main__':main(5)

#!/usr/bin/env python3
"""Fixed trusted MVP first-install entry; no production factory bypass option."""
import sys
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import installer_qualification as qualification

class MVPInputs(qualification.NativeInputs):
    directory=Path('/sources/stage/toddy-mvp-installer-native-inputs')
    def recheck(self):
        super().recheck()
        if self.manifest.get('delivery_class')!='phase2-mvp-preinstalled-v1' or self.manifest.get('g2_eligible') is not False:
            raise ValueError('Fixed MVP first-install inputs must be typed non-G2')

def main():
    if Path(__file__).resolve()!=Path('/opt/toddy-build/scripts/build/phase2/mvp_installer_qualification.py'):
        raise ValueError('Fixed root source qualification entry required')
    if sys.argv[1:2]==['collect']:
        del sys.argv[1]
        from installer_collect import main as collect
        collect(inputs_type=MVPInputs)
    else:qualification.main(inputs_type=MVPInputs)

if __name__=='__main__':main()

"""Add the managed foundation recovery entry to the measured H09 builder menu."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'h09'))
from boot_config import render as base_render

def render(filesystem_uuid,partition_uuid):
 base=base_render(filesystem_uuid,partition_uuid)
 return base+f'''\n# Retained qualified foundation image; identical original module payloads.
menuentry "Toddy OS, Linux 7.1.8-toddy (foundation recovery)" {{
    linux /boot/vmlinuz-7.1.8-toddy-foundation root=PARTUUID={partition_uuid.lower()} rootwait ro console=tty0 console=ttyS0,115200n8
}}
'''

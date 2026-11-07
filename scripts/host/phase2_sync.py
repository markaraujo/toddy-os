#!/usr/bin/env python3
"""Use the verified locked input transfer against the Phase 2 overlay VM only."""
import argparse
import phase2_vm
import sync_build

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--metadata-only', action='store_true',
                        help='Keep existing archives; each recipe still verifies its pinned bytes')
    args = parser.parse_args()
    sync_build.vm.ssh_args = phase2_vm.ssh_args
    sync_build.main(metadata_only=args.metadata_only)

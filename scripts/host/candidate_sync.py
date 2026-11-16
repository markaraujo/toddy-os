#!/usr/bin/env python3
"""Sync reviewed native candidate inputs under the existing exclusive guest lock."""
import phase2_candidate_vm as candidate
import sync_build

if __name__ == '__main__':
    candidate.owned()
    candidate.bases()
    sync_build.vm.ssh_args = candidate.ssh
    sync_build.main(metadata_only=True, include_references=False, extra_metadata=(
        'config/phase2', 'runtime', 'ui/phase2', 'assets/brand',
        'docs/evidence/B01-engine-components.json',
        'docs/evidence/B02-desktop-runtime-manifest.json',
        'tests/fixtures/voice/human'))

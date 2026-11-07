#!/bin/bash
# Run through run_step.py; both archives precede any installed ownership change.
set -euo pipefail
cd /opt/toddy-build/scripts/build
python3 h11/require_gate.py
prepared=/mnt/lfs/sources/evidence/h11-python-qa-preparation/prepared.json
if [[ ! -f $prepared ]]; then
    python3 -B prepare_python_qa.py
fi
# The transaction revalidates all ingredients and resumes only known states.
python3 -B install_python_qa.py

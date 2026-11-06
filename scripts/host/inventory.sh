#!/bin/bash
# Read-only public-safe baseline. Do not print environment or credentials.
set -uo pipefail
uname -srmo
lscpu | sed -n '1,26p'
free -h
df -hT .
if [[ -r /dev/kvm && -w /dev/kvm ]]; then echo 'KVM: read/write available'; else echo 'KVM: unavailable'; fi
for tool in gcc g++ make bison gawk m4 texi2any qemu-system-x86_64 qemu-img docker git python3; do
    if command -v "$tool" >/dev/null; then "$tool" --version | head -1; else echo "MISSING: $tool"; fi
done
if sudo -n true 2>/dev/null; then echo 'sudo: noninteractive available'; else echo 'sudo: authentication required'; fi
docker info --format 'Docker server: {{.ServerVersion}}'

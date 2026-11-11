"""Expose only the verified Samba build output through its read-only legacy path."""
import hashlib
from pathlib import Path
import subprocess
import sys

BASE_SHA = "5c0e75e5774d54ae734c3a9587dc511431c0357a1ce47e62b01a18a223039410"
PROFILE_SHA = "ff674ce4db4e3f47e55aefec9e7160c6536f9111d137ecabebc7c5a9923e61d0"
SOURCE = "/mnt/lfs/sources/phase2/inputs/samba-4.24.6-build-alias"
WORK = "/mnt/lfs/sources/phase2/work/samba-1"


def profile(source):
    assert hashlib.sha256(source).hexdigest() == BASE_SHA
    text = source.decode()
    marker = 'readonly_bind "$TODDY_INPUT" "$root/src"\n'
    assert text.count(marker) == 1
    extension = '''# Samba's generated WSP code includes bin/default paths relative to the
# source. Expose only the existing configured output via this read-only
# alias. The same worker remains writable through /build.
if [[ "$TODDY_INPUT" == /mnt/lfs/sources/phase2/inputs/samba-4.24.6-build-alias ]]; then
    [[ "$TODDY_WORK" == /mnt/lfs/sources/phase2/work/samba-1 ]]
    [[ -d "$TODDY_INPUT/bin" && ! -L "$TODDY_INPUT/bin" ]]
    [[ -z $(find "$TODDY_INPUT/bin" -mindepth 1 -print -quit) ]]
    [[ -d "$TODDY_WORK/probe-configured" && ! -L "$TODDY_WORK/probe-configured" ]]
    [[ -f "$TODDY_WORK/probe-configured/.lock-wscript" ]]
    readonly_bind "$TODDY_WORK/probe-configured" "$root/src/bin"
fi
'''
    result = text.replace(marker, marker + extension).encode()
    assert hashlib.sha256(result).hexdigest() == PROFILE_SHA
    return result


if __name__ == "__main__":
    arguments = sys.argv[1:]
    identities = arguments[1:3] if arguments[:1] == ["--loopback"] else arguments[:2]
    assert identities == [SOURCE, WORK]
    base = Path(__file__).with_name("isolated.sh")
    result = subprocess.run(["bash", "-s", "--", *arguments], input=profile(base.read_bytes()))
    raise SystemExit(result.returncode)

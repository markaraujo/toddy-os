"""Require the byte-exact client payload and completed private SMB exchange."""
import hashlib
import json
from pathlib import Path

from verify_stage import inspect_stage

WORK = Path('/mnt/lfs/sources/phase2/work/samba-1')
LOG = Path('/var/log/toddy/phase2')


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def qualify():
    selected = WORK / 'samba-client-selected-stage-2.json'
    assert digest(selected) == '36d72332929b06db5c4b2729e5bb4d5f949bf77137344840ac084abee2315f2a'
    result = json.loads(selected.read_text())
    assert result['regular_file_count'] == 80 and result['cli_version'] == 'Version 4.24.6'
    assert result['consumer'] == 'Samba shared SDK version, null-context refusal and two context lifecycles passed\n'
    for name in ('samba-configure-7', 'samba-stage-network-1', 'samba-client-select-stage-2'):
        assert (LOG / (name + '.exit')).read_text().strip() == '0'
    wire = LOG / 'samba-wire-5.json'
    assert digest(wire) == '6c3d4aac9100b3b97cf7e006a6e2a0ce869836eb135df6a7779c5918090aa591'
    record = json.loads(wire.read_text())
    assert record['state'] == 'complete' and record['exit'] == 0
    assert digest(LOG / 'samba-wire-5.log') == record['log_sha256']
    proof = json.loads((WORK / 'smb-wire-5/results.json').read_text())
    assert all(proof[k] is True for k in ('wrong_auth_refused_without_effect', 'stopped_server_refused', 'reconnected_after_restart'))
    assert proof['upload_download_delete_sha256'] == '12d09fb76c822901607aca8312d0c57d9aaed3b1e3adc78f93e2bc29826991e7'
    assert not (WORK / 'smb-wire-5/auth').exists() and not (WORK / 'smb-wire-5/private/smbpasswd').exists()
    stage = inspect_stage(WORK / 'stage-client-2')
    assert stage['manifest_sha256'] == '9d3aec1d9af08a6a9195608a636371f10616bcfa6f63ae09b81090bdadb09b40'
    return stage['entries']

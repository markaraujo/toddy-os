"""One bounded metadata-only recovery; never rebuild or rerun accepted programs."""
from pathlib import Path
import hashlib
import json


def files(base, elf=False):
    return {
        str(p.relative_to(base)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in base.rglob('*')
        if p.is_file() and not p.is_symlink()
        and (not elf or p.open('rb').read(4) == b'\x7fELF')
    }


def main(recipe):
    work = Path('/build')
    receipt = work / 'before-metadata-4.json'
    assert not receipt.exists() and not (work / 'stage-results.json').exists()
    previous = json.loads((work / 'before-collect-3.json').read_text())
    assert files(work / 'compile', True) == previous['artifacts']
    assert files(Path('/stage')) == previous['stage_sha256']
    logs = dict(previous['reused_logs'])
    for name in ['local-probe', 'local-probe.log', 'actual-version.log']:
        logs[name] = hashlib.sha256((work / name).read_bytes()).hexdigest()
    assert all(hashlib.sha256((work / n).read_bytes()).hexdigest() == h
               for n, h in logs.items())
    receipt.write_text(json.dumps({'retained': logs, 'metadata_only': True}, indent=2) + '\n')
    # Execute only the final Python collector, never shell/compiler/test commands.
    marker = "python3 - <<'PY'\n"
    assert recipe.count(marker) == 1 and recipe.endswith('\nPY\n')
    collector = recipe.split(marker, 1)[1][:-4]
    exec(compile(collector, '<retained-kerberos-metadata>', 'exec'), {})
    result = json.loads((work / 'stage-results.json').read_text())
    assert result['artifacts'] == previous['artifacts']
    assert result['stage_sha256'] == previous['stage_sha256']
    assert all(hashlib.sha256((work / n).read_bytes()).hexdigest() == h
               for n, h in logs.items())
    (work / 'metadata-4-retained.json').write_text(json.dumps({
        'compiler_ELFs_unchanged': len(previous['artifacts']),
        'stage_files_unchanged': len(previous['stage_sha256']),
        'logs_and_consumer_unchanged': logs,
        'no_compiler_test_stage_or_consumer_execution': True,
    }, indent=2) + '\n')

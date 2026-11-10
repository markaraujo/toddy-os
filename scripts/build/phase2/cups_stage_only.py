"""Bounded first staging/consumer recovery; retain every original test result."""
from pathlib import Path
import ast
import hashlib
import json
import subprocess


def files(base, elf=False):
    return {str(p.relative_to(base)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in base.rglob('*') if p.is_file() and not p.is_symlink()
            and (not elf or p.open('rb').read(4) == b'\x7fELF')}


def main(recipe):
    work = Path('/build')
    receipt = work / 'before-stage-5.json'
    assert not receipt.exists() and not (work / 'stage-results.json').exists()
    assert not list((work / 'stage').iterdir())
    assert not (work / 'original-stage.log').exists() and not (work / 'local-probe').exists()
    original = json.loads((work / 'before-finish-4.json').read_text())
    before = files(work / 'tree', True)
    assert all(before[k] == value for k, value in original['artifacts'].items())
    assert all(hashlib.sha256((work / name).read_bytes()).hexdigest() == value
               for name, value in original['reused_logs'].items())
    assert hashlib.sha256(Path('/src/cups/testsnmp.c').read_bytes()).hexdigest() == '72cea705af27270d3969899334fc7a20b5280dc133d65026a35a7c3999d93d3e'
    raw = json.loads((work / 'original-local-tests.json').read_text())
    assert hashlib.sha256(json.dumps(raw, sort_keys=True, separators=(',', ':')).encode()).hexdigest() == '2e28fd9a2b7231fb7b5f6c301986469c4b4d1f0b574082e09acff139bd821da2'
    collector = recipe.split("python3 - <<'PY'\n")[-1].rsplit('\nPY', 1)[0]
    function = next(n for n in ast.parse(collector).body if isinstance(n, ast.FunctionDef) and n.name == 'select_local_results')
    namespace = {}
    exec(compile(ast.Module(body=[function], type_ignores=[]), '<CUPS-result-selection>', 'exec'), namespace)
    selected, diagnostic = namespace['select_local_results'](raw, (work / 'testsnmp.log').read_text())
    assert len(selected) == 9 and not diagnostic['qualified']
    names = ['original-build.log', 'original-test-build.log', 'original-local-tests.json', 'testsnmp.log']
    names += [row['name'] + '.log' for row in selected if not row.get('reused_original_make_log')]
    logs = {name: hashlib.sha256((work / name).read_bytes()).hexdigest() for name in names}
    receipt.write_text(json.dumps({'artifacts': before, 'retained_logs': logs,
                                  'raw_result_rows': len(raw), 'selected_local_programs': 9}, indent=2) + '\n')
    marker = '# Preserve compiled lp/lpadmin policy'
    assert recipe.count(marker) == 1
    subprocess.run(['bash', '-euo', 'pipefail', '-c', 'cd /build/tree\n' + recipe[recipe.index(marker):]], check=True)
    assert files(work / 'tree', True) == before
    assert all(hashlib.sha256((work / name).read_bytes()).hexdigest() == sha for name, sha in logs.items())
    result = json.loads((work / 'stage-results.json').read_text())
    assert result['raw_original_results'] == raw and len(result['original_tests']) == 9
    (work / 'stage-5-retained.json').write_text(json.dumps({
        'compiler_ELFs_unchanged': len(before), 'all_test_logs_unchanged': logs,
        'raw_ten_result_rows_retained': True, 'no_original_test_or_main_compiler_execution': True,
    }, indent=2) + '\n')

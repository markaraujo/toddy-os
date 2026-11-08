"""Keep passed tool consumers; finish only Rustdoc after Clippy text normalization."""
import ast
import hashlib
import json
import os
from pathlib import Path
import resource
import subprocess
import sys


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def entries():
    rows = {}
    for path in sorted(Path('/stage').rglob('*')):
        if path.is_symlink():
            rows[str(path.relative_to('/stage'))] = {'symlink': os.readlink(path)}
        elif path.is_file():
            rows[str(path.relative_to('/stage'))] = {'sha256': digest(path), 'size': path.stat().st_size}
    return rows


def main():
    assert os.getuid() == 101
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    probe, previous_probe = sys.argv[1:]
    assert previous_probe == probe.replace("101, 'clippy::eq-op'", "101, 'clippy::eq_op'")
    prior = Path('/build/stage-tests-recovery-7')
    consumer = Path('/build/tool-consumers-7')
    assert (prior / 'tools.exit').read_text().strip() == '1'
    text = (prior / 'tools.log').read_text()
    assert text.rstrip().endswith("AssertionError: ('clippy-reject', 'required result absent')")
    assert "assert contains in text, (name, 'required result absent')" in text
    negative = (consumer / 'clippy-reject.log').read_text()
    assert 'error: equal expressions as operands to `==`' in negative
    assert 'requested on the command line with `-D clippy::eq-op`' in negative
    cargo = (consumer / 'cargo-test.log').read_text()
    assert cargo.count('test result: ok. 1 passed; 0 failed;') == 2
    versions = json.loads((consumer / 'versions.json').read_text())
    assert versions['rustc'].startswith('rustc 1.97.1 ')
    assert versions['cargo'].startswith('cargo 1.97.1 ')
    assert "pub fn invalid(a:i32)->bool { a == a }" in (consumer / 'src/lib.rs').read_text()
    before = entries()
    assert before == json.loads((prior / 'stage-before.json').read_text())
    assert before == json.loads(Path('/build/stage-tests-recovery-6/stage-before.json').read_text())
    stat = os.statvfs('/build')
    assert stat.f_bavail * stat.f_frsize >= 17 * 1024**3
    work = Path('/build/tool-docs-8')
    assert not work.exists()
    work.mkdir()
    originals = [node.value.value for node in ast.walk(ast.parse(probe))
                 if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'original'
                                                        for t in node.targets)
                 and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str)]
    assert len(originals) == 1
    source = work / 'lib.rs'
    source.write_text(originals[0])
    with (work / 'rustdoc.log').open('xb') as output:
        result = subprocess.run(['/stage/usr/bin/rustdoc', '--edition', '2024',
                                 '--crate-name', 'toddy_tool_probe', str(source),
                                 '-o', str(work / 'doc')], stdout=output, stderr=subprocess.STDOUT)
    (work / 'rustdoc.exit').write_text(str(result.returncode) + '\n')
    assert result.returncode == 0
    html = work / 'doc/toddy_tool_probe/fn.add.html'
    assert html.is_file() and 'Add two native values.' in html.read_text()
    assert before == entries(), 'Tool consumers modified the SDK stage'
    checks = [{'name': name, 'expected_exit': expected,
               'qualification': 'Preserved job7 runner reached the subsequent Clippy text assertion; no separate per-command exit file',
               'log_sha256': digest(consumer / (name + '.log'))}
              for name, expected in [('c-ffi-compile',0),('c-ffi-archive',0),
                                     ('rustfmt-reject',1),('rustfmt-format',0),('rustfmt-check',0),
                                     ('cargo-test',0),('cargo-clippy',0),('clippy-reject',101)]]
    checks.append({'name':'rustdoc','native_exit':result.returncode,
                   'log_sha256':digest(work / 'rustdoc.log'),'html_sha256':digest(html)})
    proof = {'scope':'Derived qualification of preserved real native tool consumers plus Rustdoc-only completion',
             'original_install_exit':0,'original_wrapper_exits':{'stage4':1,'guard5':1,'probe6':1,'collector7':1},
             'previous_collector_cause':'Clippy normalizes diagnostic option eq_op to eq-op; expected101 already observed by runner',
             'qualification_exit':0,'rustdoc_native_exit':result.returncode,
             'probe_sha256':hashlib.sha256(probe.encode()).hexdigest(),
             'original_probe_sha256':hashlib.sha256(previous_probe.encode()).hexdigest(),
             'previous_tools_log_sha256':digest(prior / 'tools.log'),
             'install_log_sha256':digest(Path('/build/stage-tests-4/install.log')),
             'versions':versions,'checks':checks,'stage_unchanged_by_probe':True,
             'entries':before}
    stat = os.statvfs('/build')
    proof['free_bytes_after_probe'] = stat.f_bavail * stat.f_frsize
    assert proof['free_bytes_after_probe'] >= 16 * 1024**3
    (work / 'qualified.json').write_text(json.dumps(proof,indent=2)+'\n')
    print(json.dumps({k:v for k,v in proof.items() if k!='entries'}),flush=True)


if __name__ == '__main__':
    main()

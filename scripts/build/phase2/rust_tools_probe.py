"""Real offline Rust tools/FFI consumers, reusable after owned installation."""
import json
import os
from pathlib import Path
import subprocess
import sys


def main():
    prefix = Path(sys.argv[1])
    work = Path(sys.argv[2])
    assert str(prefix) in ['/stage/usr', '/usr']
    assert work.is_absolute() and not work.exists()
    assert work.is_relative_to('/build') or work.is_relative_to('/tmp')
    work.mkdir()
    env = dict(os.environ, PATH=str(prefix / 'bin') + ':' + os.environ['PATH'],
               RUSTC=str(prefix / 'bin/rustc'), RUSTDOC=str(prefix / 'bin/rustdoc'),
               CARGO_HOME=str(work / 'cargo-home'), CARGO_NET_OFFLINE='true',
               CARGO_BUILD_JOBS='4', RUST_TEST_THREADS='4')
    versions = {}
    for name in ['rustc', 'cargo', 'rustdoc', 'rustfmt', 'clippy-driver']:
        versions[name] = subprocess.check_output([str(prefix / 'bin' / name), '--version'],
                                                env=env, text=True).strip()
    (work / 'versions.json').write_text(json.dumps(versions, indent=2) + '\n')
    assert versions['rustc'].startswith('rustc 1.97.1 ')
    # Cargo has its own package patch version: this authenticated Rust1.97.1
    # source contains Cargo0.98.0, rendered by cargo/version.rs as1.97.0.
    assert versions['cargo'].startswith('cargo 1.97.0 ')
    assert versions['rustdoc'].startswith('rustdoc 1.97.1 ')
    verbose = subprocess.check_output([env['RUSTC'], '-vV'], env=env, text=True)
    assert 'LLVM version: 22.1.8' in verbose
    (work / 'Cargo.toml').write_text('[package]\nname="toddy-tool-probe"\nversion="0.1.0"\nedition="2024"\n')
    (work / 'src').mkdir()
    lib = work / 'src/lib.rs'
    original = '''/// Add two native values.
/// ```
/// assert_eq!(toddy_tool_probe::add(20, 22), 42);
/// ```
pub fn add(a:i32,b:i32)->i32 {a+b}
#[link(name="toddyffi",kind="static")]
unsafe extern "C" { fn toddy_twice(value:i32)->i32; }
pub fn twice(value:i32)->i32 { unsafe {toddy_twice(value)} }
#[cfg(test)] mod tests {
#[test] fn native_ffi_and_thread() {
assert_eq!(super::twice(21),42);
assert_eq!(std::thread::spawn(|| super::add(20,22)).join().unwrap(),42);
}}
'''
    lib.write_text(original)
    (work / 'ffi.c').write_text('int toddy_twice(int value) { return value*2; }\n')
    rows = []

    def run(name, command, expected=0, contains=None):
        result = subprocess.run(command, cwd=work, env=env, capture_output=True, text=True)
        text = result.stdout + result.stderr
        (work / (name + '.log')).write_text(text)
        assert result.returncode == expected, (name, result.returncode)
        if contains is not None:
            assert contains in text, (name, 'required result absent')
        rows.append({'name': name, 'exit': result.returncode, 'expected_exit': expected})
        return text

    run('c-ffi-compile', ['cc', '-fPIC', '-c', 'ffi.c', '-o', 'ffi.o'])
    run('c-ffi-archive', ['ar', 'crs', 'libtoddyffi.a', 'ffi.o'])
    env['RUSTFLAGS'] = '-L native=' + str(work)
    run('rustfmt-reject', [str(prefix / 'bin/rustfmt'), '--edition', '2024', '--check', str(lib)], 1)
    run('rustfmt-format', [str(prefix / 'bin/rustfmt'), '--edition', '2024', str(lib)])
    run('rustfmt-check', [str(prefix / 'bin/rustfmt'), '--edition', '2024', '--check', str(lib)])
    output = run('cargo-test', [str(prefix / 'bin/cargo'), 'test', '--offline'])
    assert output.count('test result: ok. 1 passed; 0 failed;') == 2, 'Unit and doctest must both run'
    run('cargo-clippy', [str(prefix / 'bin/cargo'), 'clippy', '--offline', '--all-targets', '--', '-D', 'warnings'])
    formatted = lib.read_text()
    lib.write_text('pub fn invalid(a:i32)->bool { a == a }\n')
    run('clippy-reject', [str(prefix / 'bin/cargo'), 'clippy', '--offline', '--', '-D', 'clippy::eq_op'],
        101, 'clippy::eq_op')
    lib.write_text(formatted)
    run('rustdoc', [env['RUSTDOC'], '--edition', '2024', '--crate-name', 'toddy_tool_probe',
                    str(lib), '-o', str(work / 'doc')])
    assert (work / 'doc/toddy_tool_probe/fn.add.html').is_file()
    assert 'Add two native values.' in (work / 'doc/toddy_tool_probe/fn.add.html').read_text()
    proof = {'scope': 'Actual offline Cargo unit/doctest + C static FFI/thread, '
             'Clippy success/rejection, Rustfmt rejection/format/check, Rustdoc HTML',
             'prefix': str(prefix), 'versions': versions, 'rustc_verbose': verbose, 'checks': rows}
    (work / 'results.json').write_text(json.dumps(proof, indent=2) + '\n')
    print(json.dumps(proof), flush=True)


if __name__ == '__main__':
    main()

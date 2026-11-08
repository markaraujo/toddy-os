"""Partition qualified LLVM shared runtime from its build-only SDK stage."""
from pathlib import Path
import hashlib


def split_runtime(compiler: Path, runtime: Path):
    library=compiler/'usr/lib/libLLVM.so.22.1'
    link=compiler/'usr/lib/libLLVM.so'
    assert library.is_file() and not library.is_symlink(), 'Expected LLVM22.1 ABI payload'
    assert link.is_symlink() and link.readlink()==Path('libLLVM.so.22.1'), 'Unexpected LLVM linker alias'
    assert not runtime.exists() and not runtime.is_symlink(), 'Reconcile existing runtime stage; no replay'
    assert not any(p.is_symlink() for p in [compiler,compiler/'usr',compiler/'usr/lib']), 'Stage directory alias refused'
    with library.open('rb') as stream:before=hashlib.file_digest(stream,'sha256').hexdigest()
    target=runtime/'usr/lib';target.mkdir(parents=True)
    library.rename(target/library.name);link.rename(target/link.name)
    with (target/library.name).open('rb') as stream:after=hashlib.file_digest(stream,'sha256').hexdigest()
    assert before==after and (target/link.name).readlink()==Path('libLLVM.so.22.1')
    assert (target/link.name).resolve()==(target/library.name).resolve()
    return {'abi':'22.1','library_sha256':after,'payload':['usr/lib/libLLVM.so.22.1','usr/lib/libLLVM.so'],
            'scope':'Shared runtime only; compiler/headers/libclang/tools remain in build-only llvm package'}

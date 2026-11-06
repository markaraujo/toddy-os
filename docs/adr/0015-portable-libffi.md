# ADR-0015: Generic Libffi for the experimental x86-64 image

- Status: Accepted for implementation; target tests remain required
- Date: 2026-11-06
- Scope: H07 final Libffi 3.8.0

## Context

The experimental image must not silently require the build workstation's CPU
extensions. Frozen LFS 13.1-systemd section 8.51 warns that Libffi's default
native optimization can produce illegal instructions on less capable CPUs.
It explicitly permits --without-gcc-arch for a generic library when a shared
CPU architecture cannot be assumed. The guest CPU currently reflects the
AMD build host; that is not evidence for other physical machines.

## Decision

Build the frozen Libffi 3.8.0 with --without-gcc-arch and --disable-static.
Keep the full upstream make check results and compile/run an actual ffi_call
probe against the installed native library. Do not infer physical hardware
support from those VM tests. Source archive/version and the rest of the book
recipe remain unchanged.

## Alternatives and consequences

--with-gcc-arch=native could optimize this VM, but unnecessarily binds the
release to its CPU. A chosen narrower architecture is possible, but the
book's explicit generic option avoids inventing a hardware baseline before
physical testing. Generic code may lose performance; correctness and release
portability take priority. Final package/ELF audits and VM boot tests still
apply. No test is disabled and no acceptance criterion is reduced.

## Primary source

[LFS 13.1-systemd, section 8.51, Libffi](https://www.linuxfromscratch.org/lfs/view/13.1-systemd/chapter08/libffi.html),
frozen locally under .local/books/lfs/13.1/chapter08/libffi.html; book hashes
are recorded in config/books.lock.json.

# ADR-0115: Preserve GI assertions with Setuptools 84 compiler dispatch

- Date: 2026-11-07 America/Sao_Paulo
- Status: Accepted after actual native correction and production preprocessing
- Scope: GI 1.86.0 test fixture only; no production source/core dependency upgrade

GI 1.86.0 compiled/staged in the descriptor-safe native namespace. Eleven of
12 selected groups passed; test_ccompiler.py failed because its two command-capture
helpers mock CCompiler.spawn. The already accepted Setuptools 84.0.0 dispatches
both Unix preprocessing and compilation through CCompiler.call. Fake compiler
names/flags were actually executed instead of intercepted. Sources:
[GI 1.86.0](https://download.gnome.org/sources/gobject-introspection/1.86/gobject-introspection-1.86.0.tar.xz)
and [Setuptools 84 Unix compiler](https://github.com/pypa/setuptools/blob/v84.0.0/setuptools/_distutils/compilers/C/unix.py),
both pinned in the current source locks. Read target code directly.

Preserve original source, raw failed logs and the eleven unchanged passes. In a
disposable validation copy, replace exactly the two mock targets spawn -> call.
Keep every assertion and the original two skips/two expected failures. The first
correction adapted preprocessing only and exposed the same compile-hook change;
that failed correction is retained. The second covered both helpers and passed:
19 tests, two upstream skips/two expected failures unchanged, exit zero.
A separate actual production CCompiler preprocessing call passed macro expansion
and comment-preservation postconditions. No compiler/runtime code was changed.

The deterministic adapter pins original test bytes, Setuptools version, original
log, exact corrected bytes/output and production preprocessing exit. Native
installation requires this composite evidence and exact adapter identity, rather
than rewriting the original failed result or rerunning all unchanged groups.
Optional doctool/docwriter was disabled and is outside the selected scanner proof;
no GTK/Cairo or broad desktop acceptance is claimed. Actual GLib metadata generation
and native Python/GIO consumer validation remain required before B01 completion.

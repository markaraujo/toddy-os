# ADR-0194 — Owned xsltproc build SDK and honest original-test results

Date: 2026-11-10
Status: Accepted scoped build SDK; four DocBook golden comparisons unaccepted

## Concrete dependency

GNOME Terminal3.60.0 initial Meson configuration found all nine runtime SDKs but
failed because `xsltproc` was absent. Actual `src/meson.build` invokes it with
`--nonet` to generate two GTK menu resources even with documentation disabled.
No Terminal compilation/test/stage/install occurred. Preserve that failed setup
and resume the same directory after this dependency; do not re-extract/rebuild.

Use frozen BLFS13.1-systemd `general/libxslt.html`1.1.45, source SHA256
`9acfe68419c4d06a45c550321b3212762d92f41465062ca4ea19e632ee5d216e`,
book page SHA256
`011a30cdc3794f2047578347ab1a20adc1b67cbcea95cadd42e09e567f7ca8ae`.
Official HTTPS archive matched frozen MD5 before extraction. Existing owned
libxml2-2.15.3 is unchanged; shared release library/CLI, static libraries and
optional deprecated Python/crypto/plugins disabled. Exact source Copyright and
leading runtime notices retained. This is a development build SDK; no Terminal
runtime dependency should force it into the offline/live root. Final image root
closure must verify that separation, rather than copying the development root.

## Real original outcomes, not make's exit alone

Isolated compile/stage/selected consumer0:41ELFs/92staged files. Original
`make check` exited0. Thread/xmlspec/multiple/XInclude/XSLTMark/DocBook/fuzz/core
programs ran, and the core driver reported748cases/noerrors. A source-dependent
German-locale conditional is not independently asserted; no separate locale pass.

The shell DocBook recipes swallow `diff` failures. Actual full log contains four
hunks at157/398/158/64: HTML, FO, XHTML and chunk output preserve11spaces before
`http://sourceware.cygnus.com/docbook-tools/`. The source `gdp-handbook.xml` has
`url="` followed by a newline and ten indentation spaces. XML attribute whitespace
normalization explains the emitted space sequence; the retained golden has none.
No stylesheet, golden, parser or foundation was changed to suppress this.
These four comparisons remain **unaccepted**, not full-suite passes. Review code
binds the exact original log/fixture hashes and refuses any broader differences.
It does not normalize outputs and report them as passed.

Scope is authenticated source UI generation, not general DocBook rendering.
The selected bounded CLI consumer performs real UTF8 transformation, refuses
malformed XML and EXSLT file writes without creating the destination, and proves
two recovery cycles. Flags are explicit `nonet/nowrite/nomkdir/maxdepth128/maxvars4096`.
They do not turn arbitrary default CLI/API calls into a general sandbox. Compilation
and checks use UID101/read-only source/no-route namespaces; runtime menu generation
must still verify real outputs and native Terminal UI, not inherit these claims.

## Native package and recovery

Initial promotion failed before archive/dpkg with own undefined metadata-log path
variable: recipe1/postnull/rootchanged0. Exact staged source entries plus one empty
doc directory verified, package/archive absence checked. Correct only the path and
resume that staging in fresh controlled install2, without deleting/copying source
stage or replaying compiler/tests. Native install2/post0/0 changed175paths/
181owned entries; actual installed UID101/no-route CLI/typed output/refusal/no-effect/
recovery/shared ABI/pkg-config/APT0. Package ships this original-test review and
build-only scope. Full-root transaction verification retained.

[Source, original log, pending goldens and native proof](../evidence/B02-libxslt-install.json).
Archive SHA256
`9110f98d8f1fbb03f0753abce5f334b9d897cb43e08988e4e2e601516f6e5147`;
raw evidence SHA256
`5e51a0eea1ce6084e72c1ee9a73873f2fc76ed2b59260a84018733cbe9cccd3e`.
No native Terminal widget/focus/login/GUI criterion is completed by this SDK.

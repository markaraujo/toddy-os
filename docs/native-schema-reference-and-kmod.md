# Native cache preflight corrections

Actual MVP base/live requirements stopped before writes on the empty input
namespace for `/usr/lib/gnome-terminal/gschemas.compiled`. A read-only aggregate
review of every selected generated output found two concrete issues, shared by
both closures. No cache producer, package install or image retry ran in this review.

GNOME Terminal **3.60.0**, frozen `src/meson.build` lines 419–429, builds its private
reference database from `org.gnome.Terminal.gschema.xml` and `external.gschema.xml`
with explicit `--schema-file` arguments, installing it in the package library
directory. `src/terminal-settings-utils.cc` loads this reference source with a null
parent. The installed runtime XML is in the global schema directory; the private
reference database is immutable package data. Pointing that private database at
the global union would change its meaning and cannot recover the missing external
reference XML.

The exact private path is therefore classified as immutable, pinned to its actual
native archive-owned SHA256
`4dcfd88b0cb247d76075060923020b286fe22075992377c9fad51f55fe4debb5`.
Its selected archive/record/source and full-image byte/mode/owner verification
remain required. A different private reference hash is refused. The global schema
cache and every other unknown private cache retain complete namespace/regeneration
requirements; there is no generic empty-cache exemption.

The second issue affects the eleven selected kernel `modules.*` cache outputs.
Frozen **kmod 34.2** owns `/usr/sbin/depmod` as the symlink `../bin/kmod`, while the
regular `/usr/bin/kmod` is archive-owned. Frozen `tools/kmod.c` dispatches these
compatibility commands from `argv[0]`; `kmod depmod` is not equivalent. The native
Coreutils **9.11** `env --help` confirms its frozen `--argv0` option. The fixed producer is:

```text
/usr/bin/env --argv0=depmod /usr/bin/kmod -a 7.1.8-toddy
```

Both executable files must be selected, regular, canonical and equal their owned
hashes before execution, in both candidate qualification and NativeFinalizer.
No arbitrary symlink execution is allowed and no declarative input supplies argv.

An in-memory read-only application of the proposed source functions to actual
selected records validates all 19 remaining cache bindings in both the base
(144220 owned entries) and live (149534 entries) closure. This is input derivation
proof only, not successful producer regeneration or native image acceptance.
The corrected packaged payload/finalizer bytes require a fresh installer package
and fresh matching projection/export inputs before composition. Preserve the
failed requirements log and all existing generations; do not relabel or overwrite
an old projection whose installer record names the earlier package revision.

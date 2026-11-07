# ADR-0114: Native runtime bootstrap without changing foundation ABI

- Date: 2026-11-07 America/Sao_Paulo
- Status: Accepted implementation choice; Node/native bridge spikes still pending
- Scope: B01 GLib/introspection/PyGObject/Node bootstrap, not a new architecture

Reuse accepted Python 3.14.10, GCC 16.2.0, Glibc 2.44, libffi 3.8.0, PCRE2 10.49,
libmount/zlib and native build/package tools. GLib/GIO and Node were actually
absent from the accepted clone. No accepted foundation package is rebuilt or
silently upgraded to supply them.

Use the pinned [BLFS 13.1-systemd](https://www.linuxfromscratch.org/blfs/view/13.1-systemd/)
GLib 2.88.3, GObject Introspection 1.86.0 and PyGObject 3.56.3 candidates. GLib's
first owned bootstrap omits introspection metadata until the scanner is available.
Build the scanner without its duplicate core introspection payload, then generate
the matching GLib metadata and upgrade GLib under the same package ownership.
GTK/Cairo remain later consumers, not mandatory dependencies of the headless GIO
spike. Do not use host Python/GIO success as native acceptance.

Node 24.19.0 is the frozen book candidate and satisfies Pi 1.5.0's >=22.19.0
requirement. Use its source-bundled private libraries for this bootstrap, rather
than replacing accepted OpenSSL 4.0.3 or guessing that an upstream shared-OpenSSL
configuration is qualified. Those dependencies retain Node's complete bundled
license notices and are independently tracked; no system ABI files are replaced.
No npm/Corepack runtime is required by the packaged worker. The exact 88-package
Pi npm closure is acquired with lifecycle scripts disabled and byte-verified
against integrity-pinned archives. Optional Kerberos/proxy authentication is not
qualified or silently installed. This choice adds no mandatory hosted provider.

[Node v24.19.0 BUILDING.md](https://github.com/nodejs/node/blob/v24.19.0/BUILDING.md)
specifies GCC >=12.2 and typically >=8 GB RAM for four parallel jobs. The actual
12-GiB build VM uses four Node jobs. It is separate from the 4-vCPU/8-GiB product
runtime reference. Retain generic x64 compilation without -march=native; verify
actual binary/runtime CPU compatibility before claiming that profile supported.
The unmodified source is mounted read-only; Node's generated configure outputs
use a disposable writable build copy. Source and runtime measurements remain distinct.

The qualified compile namespace provides only read-only /usr/source inputs and
writable build/stage/tmp, no private roots/bus/credentials or external network.
Actual native UID/GID 101 has zero effective/permitted capabilities and no new
privileges. Only root entry's chroot/setuid/setgid transitions are retained before
that drop. Compile containment does not qualify package-manager side effects:
unqualified transactions still use existing native backend plus full-root diffs,
source/ownership/notices and direct consumer postchecks (ADR-0110).

The source lock records official verified bytes. Each subsequent native outcome
belongs in B01 evidence; this decision does not assert that Node, Python bindings,
GTK, the installer, a model or the full assistant already works.

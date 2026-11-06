# ADR-0056: Copy explicit live-root inventories with verified native metadata

- Date: 2026-11-06
- Status: Native copy component verified; complete image inventory/integration pending

A release root must preserve numeric ownership, special modes, ACLs, supported
extended attributes, hardlinks and timestamps while excluding unselected builder
state. Recursive copying of selected top-level directories is insufficient:
it can silently include unrelated sibling files or mounted filesystems. Copying
each file independently can also lose relationships between hardlinks.

Use the accepted source-built GNU Tar 1.35, including the frozen LFS ACL fix,
with an explicit NUL-separated inventory and no recursive descent. The inventory
contains every selected parent directory and its root. --null and
--verbatim-files-from treat option-like filenames as data. Creation uses PAX,
numeric ownership, ACLs, all xattr namespaces and sparse-file support; extraction
restores numeric owners, permissions, ACLs and xattrs and delays directory
metadata restoration until child extraction is finished. Native execution has
a clean environment through the existing package backend. The installed Tar
executable must match its own configured package record and exact tool version.

scripts/build/h10/copy_selected_root.py validates canonical relative names,
complete explicit parents and disjoint fresh stage/work paths inside the native
guest. Before copying, it refuses redirected source parents, special nodes and
filesystem crossings. Symlink leaves are copied as links, never followed.
It snapshots every selected entry's bytes/link target, mode, numeric owner,
nanosecond mtime and xattr digests, plus complete hardlink equivalence groups.
The same selected source must remain unchanged after archive creation and after
copy verification. The extracted tree is fully enumerated and must match that
snapshot, so extra files and broken hardlinks fail even if selected bytes match.

The caller still must derive the selection from accepted package/configuration
provenance, classify generated state, omit mounts/account secrets/build paths,
apply the appropriate H10/H11 gate and verify the final root inventory. This
primitive does not decide which contents are safe for publication. Fresh
accounts are a separate generated input (ADR-0055). Final Squashfs ACL sidecar
restoration remains necessary (ADR-0048); native Tar preservation does not add
unsupported ACL namespaces to Squashfs.

A private native probe copied 12 explicit entries including six regular-file
names, a hardlinked native executable, UID/GID 18 content, mode 4750, an access
ACL for UID 101, a default directory ACL, a capability xattr, a user xattr,
UTF-8/newline names, a symlink and a sparse file of 16 MiB plus three bytes.
Exact source/destination snapshots match; the sparse destination retains holes.
An omitted sibling and omitted subtree are absent. An option-like filename is
preserved literally without executing its harmless touch sentinel. Negative
cases reject traversal, a redirected parent, a FIFO, a real tmpfs filesystem
crossing and an existing destination. No failure case overwrites preserved data.
The tmpfs test runs inside a private mount namespace and is unmounted in finally;
no host/global mount or installed package is changed. Successful private fixtures
are removed after retaining the result and native create/extract logs.

Final raw report .local/logs/h10-selected-root-copy-probe.json SHA-256:
2b83f96911278f5b45418acb31113b29f77115843420ffe3e7f95ebf7a02d60d.
Tested copy component SHA-256:
4d5b634a916e346d85cffc5d293ffba4431cf49edd4caa416a4fc6abbbebc530.
Actual native Tar executable SHA-256:
1ba13a2040f171cabb594612efb9feea1f81104156603884fd22783137aad461.
Its own native archive SHA-256:
eb2755b5888c2c69a6035d3f5ceebb69d901705c008e9048b9a9da014076ace4.
Immutable SHA-256-suffixed reports are retained. Reproduce with
python3 scripts/host/probe_selected_root_copy.py. Three local boundary tests
cover names/parents, hardlink identity and refusal of redirects/special nodes.

Primary sources: frozen tar-1.35.tar.xz doc/tar.texi, --no-recursion/files-from,
PAX, ACL/xattr and sparse archive sections; the accepted native tar --help
confirms these exact flags. The no-recursion section explicitly describes using
an externally selected filename list. Source and ACL patch integrity remain
pinned in config/sources.lock.json; no version change is introduced.

Alternatives rejected are whole-directory copying (unselected state), independent
file copying (hardlink loss) and assuming archive exit 0 proves metadata fidelity
(the complete extracted inventory must match). Retaining an intermediate archive
uses extra temporary disk space but permits diagnosis/recovery without touching
the source. This experiment is not a complete root, Squashfs, ISO or boot test.
H10 and all later acceptance gates remain pending.

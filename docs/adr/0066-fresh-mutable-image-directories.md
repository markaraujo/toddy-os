# ADR-0066: Recreate mutable image directories from explicit metadata

- Date: 2026-11-07
- Status: Native component checks passed; full image and APT acquisition pending
- Extends: ADR-0057 payload selection and ADR-0065 image APT identity

The explicit payload copier preserves actual directory metadata. Although the
inventory already rejected cache/log files, it still selected owned cache/log
directories for copying. APT changes directory ownership at runtime, using the
builder's dynamically allocated _apt identity. Copying those actual directories
would therefore bypass the fresh image account policy and could preserve builder
ACLs or inappropriate numeric ownership. This is an image assembly defect found
before a release image was produced, not a failure of the running Berkeley suite.

Move package directories under var/cache, var/log and var/lib/apt into the fresh
directory plan. Keep their reviewed package metadata and reject files in these
trees; do not silently drop owned payload. Require every fresh parent to be
either explicitly planned or an owned selected directory. Other package payload
continues through the metadata-preserving copier. The inventory does not remove
or change package ownership records.

The new fresh_directories.py component runs after payload copying and before
account generation, cache generation, service configuration and final ACL capture.
It requires a private guest stage, canonical paths, known baseline numeric
identities, unchanged required runtime modes, physical parents and one filesystem.
All existing destinations, including empty directories and dangling symlinks,
are refused before mutation. Newly created directories have inherited ACLs
removed; copied parents retain their ACLs. Exact ownership/modes, no xattrs and
no unexpected child contents are checked, then directories/parents are fsynced.
An interrupted stage is preserved and rebuilt fresh, never merged or emptied.

Prepare APT's archives/partial and lists/partial as 0700, UID 100, GID 0;
lists/auxfiles is 0755, UID 100, GID 0. Parents remain 0755 root:root.
The fresh _apt user has primary GID 100, but the directories deliberately use
ROOT_GROUP as specified by frozen APT 3.0.4 apt-pkg/acquire.cc lines 97–167.
Any difference from package-time directory metadata is recorded as an explicit
runtime ownership override. Other APT directories from its package layout remain
fresh with the recorded package metadata.

Primary sources inspected locally: frozen APT 3.0.4 CMakeLists.txt directory
installation and apt-pkg/acquire.cc SetupAPTPartialDirectory/GetLock, archive
SHA-256 e853aec49afbe520ebcd4dbcbc98e1c55262c6bf1c119cf43e6aec69752443c6;
LFS 13.1-systemd section 7.5 Creating Directories, page SHA-256
88ba0fe23f1c8b0c9560375ffb427aa9bbc99602f05c4f94f6726756daf0882f.
The existing fresh root-home 0700 policy remains the ADR-0055 image choice;
the book's original directory creation uses 0750. Temporary directories retain
the book's 1777 policy.

Alternatives rejected: copying builder directories imports mutable identity/ACL
state; recursively chowning a copied tree can modify unknown data and obscure
provenance; running APT as root avoids the selected sandbox requirement; silently
deleting owned cache data would hide a package design error. Explicit fresh
directories make the runtime ownership transformations reviewable.

## Evidence and remaining acceptance

The actual 124-package candidate now selects 63,129 copy paths and 12 fresh
directories: three owned cache/log directories moved from copying to generation.
All 60,397 regular files/symlinks remain selected. The complete installed-payload
preflight still correctly refuses the unfinished shared Info index ownership
at /usr/share/info/dir; no exception was added. Native refusal report SHA-256
1d17cb902d8dde07cc8e42b8292051d63caf5b783ca9eebd153ffd447731fbbd;
candidate SHA-256 e2b4872fcb79c0dbcf878404ff13c1e9b4f249509044e627f7af3ec2933e70a6.

The separate native directory probe uses that candidate's fresh metadata plus
seven prepared APT directory rows from the frozen source layout. APT is not yet
installed: those rows are explicitly a component fixture, not an accepted
package or successful download. Nineteen directories are generated. Native
Coreutils chroot/Bash/id runs with the image's _apt UID/GID/groups 100 and writes
inside all three service directories; UID 101 cannot write them. The new files
have UID/GID 100 while directory ownership remains 100:0. A copied parent default
ACL is unchanged and does not propagate into generated children. Seven cases
are refused before any namespace mutation: existing data, redirect, missing
parent, unknown UID, traversal, incorrect runtime mode and a real tmpfs boundary.
Installed package status, accounts and source directory metadata are unchanged.

Report .local/logs/h10-fresh-directories-probe.json SHA-256:
6883e7ca3baa717eaa74fc1baadba26678dfcc42f2295805d8a0a25f32cbab70.
Helper SHA-256 b8fa4c0638c9b65a1d81e717277a796435546d21cd7c17059f7e2f9acfab9729;
inventory SHA-256 7fffc965b09f088e5c7d5d42b386ee374110e767c0ef5981f95c84d80d434091.
Six local inventory tests include mutable file rejection and missing owned parents.

The first probe incorrectly assumed the minimal runtime's dev directory was
empty; stage_runtime deliberately creates console/null device nodes. The probe
now verifies and removes only those two newly created fixture nodes before
testing full-root directory generation. Failure report SHA-256
f9fef3a5254fde0fb38eccdd8504205dd629aec7cd31472a36ff34b9c6b02ef6;
fixture /mnt/lfs/tmp/toddy-fresh-directories-9zoyrodt is preserved.

Actual APT worker identity, acquisition/signature/HTTPS checks, final image
ownership reconciliation, generated caches and native boot remain required.
This component does not accept H07, bypass H08/H09, or complete H10.

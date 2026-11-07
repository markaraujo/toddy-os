# ADR-0062: Generate the live Info index from native package documents

- Date: 2026-11-07
- Status: Native component verified; full image integration pending

The shared /usr/share/info/dir index is generated state, not one package's
immutable payload. ADR-0057 already identified the old Glibc ownership mismatch;
H07 metadata closure must remove that ownership and regenerate the installed
index before its final audit. The future live image also needs its own index,
built from exactly the documents selected for that image.

Use h10/info_index.py in a fresh private image root with an accepted package
inventory. Refuse an inventory that still owns the shared index, an existing
index, unknown files, redirected paths, altered bytes/metadata or cross-filesystem
inputs. Verify all selected document inputs and the native install-info/info
programs before generation, then verify unchanged inputs and exact output
namespace afterward. Run the actual image program in chroot with an explicit
minimal environment and a per-document deadline; do not copy the builder index
or rewrite native package metadata. Existing or partial output requires a new
stage after preserving evidence, not silent in-place repair.

The frozen inputs use uncompressed .info primary files, .info-N split parts and
illustrations. Generate entries from sorted primary documents; retain split
parts/images unchanged for the reader. Compressed inputs are explicitly refused
until a verified decompressor policy is added. Native diagnostics are retained;
only the exact no-menu-entry warning is classified, and only when the verified
input lacks START-INFO-DIR-ENTRY. Other diagnostics or nonzero exits fail.

Alternatives: copying the accumulated builder index can retain stale entries;
assigning it to one package recreates the shared-ownership defect; deleting it
without regeneration loses the documentation menu. Suppressing all stderr hides
unclassified failures. This component adapts the frozen book's optional index
recreation to an explicit verified input set with preserved diagnostics.

## Sources and native evidence

LFS 13.1-systemd section 8.73.1 documents recreating the shared index with
install-info. Frozen chapter08/texinfo.html SHA-256:
c6317cadb78a54dedd8f087d34544029a75111b4260d60fb5b5d6f5ab0a86dcb.
Texinfo 7.3 source archive SHA-256:
51f74eb0f51cfa9873b85264dfdd5d46e8957ec95b88f0fb762f63d9e164c72e.
Inspected install-info/install-info.c output_dirfile (same-directory temporary
output and rename) and the explicit zero-exit missing-entry path near line 2493.
The native info --help describes menu traversal; the probe tests that traversal
as well as direct document location and content reads.

python3 scripts/host/probe_info_index.py used actual source-owned documentation
from 40 providers, 130 document inputs and 71 primary manuals, plus verified
native programs/libraries. Two generations produced the identical 119398-byte
index, SHA-256:
5205f085d96d7b2e7fff6957993e9388cda11ad9eda82f32ebb502a94e49a6ed.
Native Info located/read the Glibc, Coreutils, Bash and Texinfo top nodes.
Following the generated Bash and Coreutils menu labels returned the exact same
document bytes as direct reads. gawknotes.info produced the sole classified
warning: its source-owned content has no directory-menu declaration. The file
is retained; no warning is silently discarded or claimed to create an entry.

Eight refusal/preservation cases passed: existing index, still-owned shared
index, unowned document, changed document, changed generator, redirected
document, redirected directory and interrupted temporary index output.
Installed index and Dpkg status remained unchanged. Successful private fixtures
were removed; complete results remain outside Git.

Final report .local/logs/h10-info-index-probe.json SHA-256:
20d3449c47e99f0cf59ac1159de1dea4683f04ac5e890c3fc47762bbe3388ce7.
Tested helper SHA-256:
af146e41588e399baea577f065cdb68b1865376d4a919edf18bd036242c857f9.

The probe deliberately selects only native document/program inputs and omits the
old installed shared index. It does not accept the full current package image,
waive the H07 Glibc index ownership mismatch, or run the pending metadata upgrade.
Production must use the post-closure accepted inventory under the H10 gate.
Whole-root assembly, loader cache generation and actual live boot remain pending.

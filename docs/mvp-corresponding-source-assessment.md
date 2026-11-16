# MVP corresponding-source assessment

This assessment does not authorize publication or claim source completeness,
reproducible binaries, a completed build, G2 or license acceptance. It separates
three different questions: actual preferred source availability; availability of
scripts/configuration needed to build/install the selected frozen software; and
byte-for-byte recovery of every historical whole-repository script fingerprint.
An unresolved fingerprint must remain visible, but it is not automatically a
missing compilation script for every package whose broad snapshot recorded it.

## Observed custody

The actual signed export2 contains329 packages. The host holds all342 unique
selected upstream source filename/SHA rows and all87 distinct audited NPM source
archives, representing88 component locations; size/SHA512/SHA256 were checked
against the actual exported agent custody. Upstream URLs are additional references
and do not replace these files. The exact329 native records and two generated
catalog proof documents were transferred with their actual digest chain.

The initial historical supporting-script audit checked2472 distinct path/hash
pairs. It found91 missing versions across47 paths, including44 versions of the
single evolving install_verified_stage.py file. These snapshots fingerprinted
many unrelated sibling scripts. Two exact versions were subsequently recovered
from the stopped builder through read-only NBD/FUSE/debugfs, with unchanged backing
image identities. One further intermediate version was reconstructed solely from
existing adjacent committed diff hunks and matched its independently pre-existing
native-record SHA. Its ancestry commits preserve the current helper at the tip.
The recovery evidence explicitly distinguishes actual snapshot reads from source
reconstruction. Neither is a native execution result.

Actual recipe_sha256/packager_sha256 entrypoints in all329 native records were
checked against committed history. The remaining recipe entrypoint mismatch is
GDM50.2 gdm-install.sh, SHA7732ee295a90729115bb9e0cdab7004a183e3dd862ce93da94d4abf9c6596997.
The current script exists and invokes the generic GDM stage installer followed by
initialize_gdm_group.py; its fingerprint differs. Current generic-stage profiles
cover146 selected packages, with zero mismatches between their declared upstream
versions and the selected versions. This is a static declaration check, not a
rebuild or proof that every required build input is present. Current GDM sources
and a current installation script are available; the historical mismatch alone
does not establish that current GDM cannot be built.

## Concrete functional inputs

The current desktop defaults upgrade unconditionally requires the previous
package/archive record. Both have now been recovered from the cold builder with
exact declared hashes:

- native-inputs/toddy-desktop-defaults_0.2.0-1+toddy1_all.deb:
  24b35fcc03fe9ad338109181552e55b07fb250a99942157f8945facecf125907,8628bytes.
- native-inputs/toddy-desktop-defaults_0.2.0-1+toddy1_all.json:
  7d40d6c20f7d8e76d8c9c344a3473c61f81ff7282ee2d53aa67dee220fff0d43,212559bytes.

These are explicit native build inputs, not Git source paths. The existing strict
source producer currently tries to resolve them through Git and therefore needs a
narrow, explicit hash-verified build-input resolver. A resolver must admit only
the exact declared previous defaults archive/record, verify native archive/control/
payload/legal custody, and retain their attribution. It must not accept arbitrary
private files, reinterpret them as source code, or omit the underlying original
project sources.

The current FUSE kernel packaging helper requires the prior native kernel archive/
record and the generated merged kernel worktree. The frozen kernel sources,
configuration/build helpers are present, but availability/regeneration of those
specific prerequisites has not been established by this assessment. Package build
inputs must be identified before claiming a functional from-source recipe set.
No mass rebuild or byte-for-byte binary reproduction is claimed.

## Minimum reviewable source mode

A useful narrowly scoped mode would retain:

1. Every exact selected upstream/NPM source and required notice/license file.
2. The full reviewed current tracked project snapshot, including current build,
   installation, patch/configuration and packaging scripts; exact historical
   original-project inputs wherever required by the actual selected payloads.
3. All329 actual native provenance records and the generated catalog attribution.
4. Explicit verified native build inputs needed by the current recipes, including
   the recovered defaults baseline and any required kernel baseline.
5. A complete unresolved historical path/SHA ledger, with per-package explanation
   of whether each mismatch affects a controlling build/install script or only an
   unrelated broad snapshot. Never erase or relabel this ledger as recovered.

Before this can become canonical corresponding-source output, review the selected
packages' controlling compilation/installation scripts, patches, configuration and
required source/build inputs. A review must identify actual included files and
explain current functional replacements; a blanket completeness boolean or a
renamed draft is insufficient. Labels cannot remedy missing required source.
The existing strict producer/publication guard must remain unchanged until an
explicit reviewed contract supports this distinction. No incomplete public bundle
or binary publication is proposed. A local review draft would have a distinct
kind and could not pass the existing package release source-inventory guard.

GPLv2 section3 includes compilation/installation scripts in complete source;
GPLv3 section1 includes the controlling scripts needed to generate/install/run/
modify the object code. Neither definition creates a requirement to reproduce
identical binary bytes. The actual package license and source correspondence must
still be reviewed, rather than inferring permission from an MVP label. Primary
texts consulted2026-11-16: [GNU GPLv2, June1991](https://www.gnu.org/licenses/old-licenses/gpl-2.0-standalone.html)
and [GNU GPLv3, June2007](https://www.gnu.org/licenses/gpl-3.0.html).

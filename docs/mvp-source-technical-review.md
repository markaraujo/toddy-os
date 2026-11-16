# Technical review of the actual MVP source assets

Scope: the signed **export2**, 329 native packages including installer version1,
source snapshot 729ad720dfa0f8ff1f2b3e105326791f6f36665b. This does not cover the
subsequent export3/installer2. The actual source inventory SHA256 is
88a949030e7861d338a87fb323556260f66b78dc0c577c1bf86ca3c9adf1a805.
The [per-package technical accounting](evidence/mvp-source-technical-accounting-1.json)
records actual material/controller/notice identities for all 329 packages.

No missing declared preferred source, current controlling script, literal project
dependency, or retained notice was identified in this accounting. This is a
technical material review, not legal advice, a clean rebuild, binary reproduction,
G2, authorization to publish or a replacement for actual coordinator signoff.
The source inventory remains a private draft with publication_eligible false.

## Actual checks

- Indexed all 28,537 source members and checked all 329 native provenance records
  against the selected archive/record identities.
- Read back/hash-checked329 copyright files and50,828 source-notice references,
  including repeated references to shared notice bytes. The source assets retain
  all 342 selected upstream archives and87 audited NPM distribution archives.
- Verified original payload-declared preferred inputs through exact committed
  source, plus the two exact recovered previous-defaults native build inputs.
- Checked current declared recipe/packager members and their project dependency
  paths;146 generic-stage upstream versions match the selected frozen versions.
- All88 unresolved historical fingerprints have actual current replacements
  included at 45 distinct paths. None is a missing-current-file placeholder.
  Per-package classification distinguishes reachable current control paths from
  unrelated whole-directory snapshot associations. Necessary current helpers are
  provided; this does not pretend that their historical byte fingerprints match.
- Rust dependencies are not omitted: Glycin/Glycin-GTK4 and librsvg include their
  exact separate vendor archives and Rust source. The Firefox source contains
  its vendor/third_party/rust material. The 87 NPM archives declare 39 MIT,
  35 Apache-2.0, 11 BSD-3-Clause, 1 Unlicense and 1 0BSD licenses in their actual package
  metadata; no .node/.wasm/.so/.dll/.exe objects were found in that closure.
  Actual package and supplemental notices remain retained, not replaced by these
  short identifiers.

The legacy named license configuration directly matches 266 package names.
Another 52 are accounted through their actual upstream per-file notices and 11
through original-material grants plus retained component notices. These are
explicit distinct bases, not invented named approvals or synthesized SPDX IDs.
The coordinator must review the actual conditions/attribution before signing off.
The full 329-row record retains the applicable named configuration where present.

## GDM, kernel and defaults

GDM is the only actual recipe entrypoint whose included current wrapper differs
from its recorded historical fingerprint. Its frozen 50.2 source/build flags and
current 50.2 generic-stage profile are included. The current wrapper invokes the
stage installer and initialize_gdm_group.py, which performs deterministic group 21
initialization matching the packaged sysusers declaration. The historical wrapper
SHA remains unresolved; this is not evidence of an omitted GDM source file or a
changed upstream version. The source/build and installation controls are present.
No PAM/login qualification is inferred from reading those controls.

The kernel source, H09 defconfig/fragment merge, explicit Landlock changes and
FUSE changes are included. Incremental cache/previous compiled objects are
workflow prerequisites; the preferred source/configuration and controlling
commands are present. This does not claim a fresh end-to-end rebuild or identical
output from today's toolchain/cache state.

The defaults 2 recipe's previous defaults 1 archive and record are included as
explicit native build inputs with exact independent hashes and verified control,
payload and legal custody. They are not misrepresented as Git source or omitted
because they are inconvenient. The original source/configuration is retained too.

## Minimum separate acceptance contract

The [pending acceptance template](templates/package-preview/current-functional-source-review.template.json)
is intentionally unusable as approval. Keep the actual source-review inventory
and historical ledger immutable. Do not rename the draft kind to make the old
strict verifier accept it. The existing strict source mode stays unchanged.

A separate reviewed current-functional mode could be accepted only after the
coordinator records a real decision against this exact asset set. Its minimal
record binds actual signed repository, source inventory, project commit,
technical report, every asset name/hash/size and every selected package identity.
Each package decision references the actual technical row and included license/
notice material; unresolved required source, patch, configuration or installation
information produces a hold. The coordinator must explicitly account for the
52 upstream-per-file and 11 original-material bases as well as the named entries.
A generic reviewed=true field, producer callback or zero-error counter is not a
substitute for that decision.

Any future publication verifier for this mode must independently re-read actual
assets/members, original source/native inputs, current project snapshot, source/
notice chains and exact package set, and verify the recorded decision. It must
retain historical_fingerprint_complete false and the full 88-entry ledger, and
claim neither historical binary reproduction nor runtime/G2 acceptance. Missing
required materials or a repository/record change invalidates the decision. A
new installer archive therefore needs its own actual changed-package accounting;
this export2 review cannot silently authorize export3.

The distinction follows the primary source definitions: GPLv2 section3 includes
compilation/installation scripts; GPLv3 section1 includes controlling scripts for
generation/installation/execution/modification. Neither text defines source
availability as identical binary output. Actual license conditions still apply:
[GNU GPLv2, June 1991](https://www.gnu.org/licenses/old-licenses/gpl-2.0-standalone.html),
[GNU GPLv3, June 2007](https://www.gnu.org/licenses/gpl-3.0.html).

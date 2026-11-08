# ADR-0129: Frozen Python test-tool backends without version drift

- Date: 2026-11-08
- Status: Accepted; native isolated and owned test-tool closure completed

Native keyboard/graphics tests need Pytest9.1.1; Mesa needs Mako1.4.1. Reuse
existing native Python3.14, packaging26.3, Setuptools84, flit_core, wheel and
MarkupSafe. Mako is independently built/owned0/0 with six actual native template
and C-code-generation consumers; no full Pytest-suite claim. Its original public
doc/build/changelog.rst is archived0600: normalize only that file0644, record its
unchanged contentSHA and preserve the failed partial copy. Do not weaken compiler
isolation or general guest/host permissions.

Freeze the exact required build/runtime backend closure in
config/phase2/python-test-tools.lock.json. Follow selected graph links or explicit
required/recommended links of one already frozen leaf with matching book hash.
Reject optional/unrelated/ambiguous/changed-parent links. This selects development
prerequisites, not every optional book dependency or a new product framework.
Keep each native package/source/version/license/owned archive independent for
reuse and change-based validation. No automatic base/live/catalog inclusion.

Trove-Classifiers2026.6.1.19's authenticated pyproject requires Calver, although
its BLFS13.1 paragraph omits that build backend. Use the official versioned
[Calver2025.10.20 source](https://pypi.org/project/calver/2025.10.20/) SHA256
c98b376c2424642224d456b2f70c51402343e008c63d204634665e1a2a2835f5.
This adds a missing build tool; it upgrades no frozen foundation component.
Retain its full Apache2 text and original source/version/provenance.

Calver's [documented SOURCE_DATE_EPOCH](https://pypi.org/project/calver/2025.10.20/)
controls the calendar date. Both its own setup.py and Trove's use_calver backend
would otherwise generate the current build date. Freeze1760918400 for Calver's
2025.10.20 and1780340400 for Trove's2026.6.1.19 (UTC hour19). Assert every wheel's
actual metadata version equals the frozen source; do not silently publish a
current-date replacement or download dependencies to bypass a mismatch.

Build in the existing qualified UID101/caps0/offline/read-only-input namespace,
using private source copies, bootstrap paths and staging. Verify source/wheel
hashes, versions and actual native backend/test consumers. Own installed packages
through controlled native transactions with retained complete notices and actual
postchecks; staging alone is not an installation-confinement proof. Keep full-root
verification until an alternative installation strategy is qualified. Preserve
raw logs and bounded failure identities. Native Pytest/backend acceptance remains
pending; this ADR does not substitute source preparation for executed tests.

## Native outcome

All12 frozen wheels and independent stages completed0, including exact Calver
2025.10.20/Trove2026.6.1.19 metadata under fixed epochs. Actual native version/
dependency closure, TOML comment-preserving edit, C lexer HTML and Pytest fixture/
parameterized pass2 plus deliberate fail1/JUnit results qualified. Owned per-package
archives installed with actual recipe/post0/0 in one34.93s full-root work slice.
Existing foundation packaging26.3/Setuptools84/flit_core reused without upgrades.
Poetry-core's vendored per-file conditions and all named source notices retained.
No full upstream, graphical, hardware or release acceptance claimed. Raw evidence
bundle and archive/source/index hashes are in B02-python-test-tools-build.json and
B02-python-test-tools-install.json. Input lock describes frozen preparation;
these measured records establish current native acceptance.

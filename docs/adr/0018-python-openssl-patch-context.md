# ADR-0018: Preserve the complete OpenSSL 4 patch on Python 3.14.10

- Status: Accepted patch adaptation; native build/full tests pending
- Date: 2026-11-06
- Scope: H07 selected Python 3.14.10 with OpenSSL 4.0.3

## Problem and experiments

The frozen LFS 13.1 Python-3.14.7-openssl_4-1.patch contains five sequential
upstream backports, including tests. Python 3.14.10 still needs their OpenSSL 4
compatibility changes. A single --dry-run of the concatenated series checks
later modifications against files without earlier applied changes and reports
extra rejected contexts. Applying the entire series for real in a separate,
archive-verified probe tree eliminates those artificial failures, but reveals
one genuine rejected test insertion: Python 3.14.10 added callback property
assignment/deletion assertions immediately before test_msg_callback_tls12.
The old insertion context no longer directly precedes that method.

The actual development recipe stopped at its dry-run with zero installed
changes. Original dry-run/real-apply outputs and rejected context are retained.
The main source tree was not compiled or installed from a partial patch.

## Decision

Retain all five upstream changes, including both added regression tests.
Adapt only the surrounding context of the test_msg_callback_exception
insertion to the newer callback property's deletion assertions. Preserve those
new upstream assertions too. Add the attributed derived patch at
patches/Python-3.14.10-openssl_4-1.patch and pin its exact SHA-256 and immutable
repository commit URL as an additional source input before the real build.
Keep the original frozen patch/source version intact in the source inventory.

Apply the complete series once, with --batch --forward --fuzz=0, to a verified
untouched source tree. Do not use a combined non-mutating dry-run as a
prerequisite for a dependent series. The isolated applied probe supplies that
preflight evidence; actual recipe exit and the complete Python suite remain
required before packaging.

## Verification and alternatives

The adapted probe applied with exit zero, zero fuzz and no rejects. All four
runtime/tool source files are byte-identical to the original patch series'
actually applied results; no C/runtime change was invented. AST inspection of
original versus adapted test_ssl.py preserves all 207 original test methods
and adds test_got_eof plus test_msg_callback_exception (209 total). No test is
removed or relaxed. The adapted SSL test source SHA-256 is
8e5fa996e2d6223c83536334c7469aafbc655fdb5ed5037218f11619fd67285d.

Derived patch SHA-256:
02a0f09dd64062891c64bd4f8fc7bb3b9a032c91e833784339bd2e3d3d35ba6f.
Probe logs, preimage/runtime hashes and AST result are preserved outside Git at
.local/logs/h07-python-compatibility. This is patch applicability/test-preservation
evidence, not a claim that Python's native build or SSL tests already passed.

Downgrading Python would abandon the selected security maintenance source.
Dropping the rejected test would reduce coverage. Increasing fuzz or ignoring
patch exit status could misapply context silently. The explicit context-only
adaptation preserves both newer Python tests and every original backport.

## Primary sources

- [LFS 13.1-systemd 8.54 Python](https://www.linuxfromscratch.org/lfs/view/13.1-systemd/chapter08/Python.html), frozen book hash in config/books.lock.json.
- Frozen Python 3.14.10 source archive and security selection: config/security-overlay.lock.json.
- Original patch in config/sources.lock.json, including its five upstream commit
  identifiers and attribution, retained verbatim apart from the documented
  context/header adaptation in the derived patch.

# ADR-0038: Preserve exact component terms and embedded bundle provenance

- Date: 2026-11-06
- Status: License inventory expanding; complete release audit remains pending

Component licenses apply individually; no proposed original-project license
relicenses the whole OS. Identify explicit upstream grants from exact frozen
COPYING/LICENSE texts and runtime headers. For mixed collections, LicenseRef
means the original per-file/embedded/documentation conditions retained in the
package and corresponding source, not a newly invented grant or a claim that
one SPDX license covers every file. Keep main-runtime and bundle terms distinct.
Absent/unreviewed components remain visibly pending until audited.

Retain numbered/v-numbered GNU COPYING files, LICENSES files/directories,
ARTISTIC, copyright notices and embedded wheel legal texts with source/path/SHA
indexes. Do not mistake Packaging's licenses Python code module for a legal-text
collection. Capture source inventory generations by content hash; do not destroy
older evidence when the scanner expands. Original program/source archives and
notice bytes remain outside Git; versions, URLs, hashes and review decisions are
committed. Corresponding-source distribution availability remains a release
obligation, not fulfilled solely by a local cache.

Python 3.14.10 includes upstream pip 26.2.2 as a pure Python wheel, with no native
extension binaries. Wheel SHA-256:
fd7f4dfa8190e014013b9f08f3e973f4e4c26ffd179a204895533a7254813a70.
Its exact vendor.txt pins 18 dependencies; their original MIT/BSD/Apache/ISC/
Python/MPL terms were read and recorded in config/component-licenses.json,
including Certifi public CA data separately from system trust. The unmodified
wheel already retains these notices; expanded packager also exports them for
inspection. No foreign distribution binary or proprietary runtime is imported.
CMake's separately recorded KWSys/KWIML/JsonCpp/cppdap/librhash choices come from
actual native CMakeCache and exact notices, not every unused Utilities source.

This source/legal review does not imply a source-built package passed native
tests, all remaining licenses are closed, original Toddy licensing D10 is
approved, or ISO/source release artifacts are already available.

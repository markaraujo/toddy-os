# ADR-0033: Freeze APT's mandatory native Triehash generator

- Date: 2026-11-06
- Status: Accepted source selection; native tests pending

Actual frozen APT 3.0.4 CMakeLists.txt requires triehash unconditionally. Select
Triehash 0.3, matching the maintained Debian source package, before building APT.
The original Perl generator archive matches SHA-256 and size published in the
Debian 0.3-3 DSC over official HTTPS. Signature not independently verified.
SHA-256: 289a0966c02c2008cd263d3913a8e3c84c97b8ded3e08373d63a382c71d2199c.
No binary package or Debian maintainer script is imported. Existing native Perl
runs the generator; compile generated C with native GCC and run upstream tests.
Retain MIT license. No hosted/build-time network fallback is allowed. Omitting
this required tool or substituting generated code would hide a build dependency.

Sources:
- https://deb.debian.org/debian/pool/main/t/triehash/triehash_0.3-3.dsc
- https://github.com/julian-klode/triehash
- https://packages.debian.org/source/trixie/triehash
- Frozen APT 3.0.4 CMakeLists.txt and Triehash 0.3 tests/run-tests.sh/framework.sh.

The unchanged Triehash test framework explicitly instruments every generator
invocation with Devel::Cover and ends by rendering coverage. Freeze Devel-Cover
1.52 and its actual required runtime/test dependency closure (16 distributions)
from original CPAN archives, verified against MetaCPAN release SHA-256 metadata.
Do not install via a moving CPAN resolver or remove instrumentation/assertions.
Native Perl 5.44 Module::CoreList determines existing core modules; include only
runtime/test/configure/build requirements, not author-only x_Dist_Zilla/develop
release tooling. Exact source versions, license identifiers, dependency edges,
probes and build order are in config/native-perl-test-tools.lock.json; complete
individual configured suites are required before package acceptance. Optional
coverage report backends remain accurately reported by upstream test skips.
These are build/test tooling; release component inclusion will be explicit.

Sources: https://metacpan.org/release/PJCJ/Devel-Cover-1.52,
https://fastapi.metacpan.org/v1/release/Devel-Cover and the exact distributions'
META.json prereqs. All source hashes are pinned before guest transfer.

Source inspection confirms default cover output inherits Html_minimal and uses
HTML::Entities, included in the frozen HTML-Parser dependency. Template Toolkit
is required by Html_basic, not the default backend; do not add an unnecessary
dependency or replace the unchanged Triehash coverage command. Native execution
of the complete tests and default report remains the acceptance requirement.

Installed-module postchecks require the loaded %INC path to be owned by the
new package in native Dpkg, preventing a pre-existing module from satisfying
acceptance accidentally. Use require for this load-only probe; full unchanged
upstream suites still exercise normal imports and coverage. Run in a private
temporary directory and remove probe-generated state. A focused existing-native
Fcntl probe passed for owner perl and rejected a deliberately wrong provider;
new CPAN packages remain unaccepted until their actual recipes/postchecks pass.
Raw .local/logs/h07-perl-module-provider-preflight.json SHA-256 8d40be86e7c3bffed1fa609e975febf8d5d2e3abf16f1eeb5530651352f76c84.

Actual first native module passed and proved source-built Dpkg routing. The next
module's suite passed but ownership preflight exposed shared perllocal.pod.
Use documented native MakeMaker NO_PERLLOCAL=1 during Makefile.PL generation;
per-module package/packlist metadata remains authoritative. Do not force-overwrite
another package's diary. The first module's +toddy1 archive removes its generated
journal while preserving original archive/source/runtime bytes; modified journal
content must refuse before upgrade. Subsequent module stages require its absence.
Native correction and retried complete tests are still acceptance work.

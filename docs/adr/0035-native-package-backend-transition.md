# ADR-0035: Switch accepted package production to native Dpkg

- Date: 2026-11-06
- Status: Implementation prepared; actual target verification pending

Once h07-dpkg.success.json proves both recipe and postcheck exit zero, dispatch
package construction/installation through source-built /usr/bin/dpkg-deb and
dpkg inside the target chroot. Validate native version and record executable/
acceptance hashes. Prior bootstrap records/archives remain unchanged and retain
builder-tool provenance. Absence of acceptance keeps explicit bootstrap routing;
an invalid present record is an error, never silent fallback.

The builder owns cache/records outside the target; native tools use a private
/sources/native-package-output directory, with hash-checked copies across that
boundary. No foreign program, maintainer script, key or host filesystem mount
is introduced. Preserve outputs on build failure for diagnosis. Installation
uses the same pre-mutation ownership rejection and conffile policy. Native Dpkg
performs dependency checking, not a simulated database edit. Record the backend
in every subsequent package record and exercise a real package recipe/postcheck
before claiming transition acceptance. Regression tests verify chroot routing,
explicit bootstrap root and invalid acceptance refusal.

The archive build/install path and raw-extraction metadata upgrade share one
private-workspace validator. Refuse symlinks, unexpected owner or non-0700
permissions before archive copy/extraction; preserve existing archive inputs for
diagnosis. Local regression probes cover refusal without writes to a symlink
target and safe directory reuse. Actual native-backend package acceptance still
requires the next successful guest recipe/postcheck after input synchronization.

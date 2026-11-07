# Large delivery releases

The repository and Pages dashboard remain the development record. GitHub Releases
provides downloadable snapshots for major accepted deliveries. See ADR-0103.
The H13 foundation candidate is `v0.1.0-foundation.1`. The tested image was built
from commit `e24e452399621607a8386db582e5776bd66994da`. The owner approved
D10's licenses on 2026-11-07; the final release source tag must include that
grant as well as the tested recipes. The draft remains under final verification.
G1 passed in QEMU/KVM; G2, physical hardware and B01-B13 remain pending. The
foundation ISO has a command-line live system without persistence, desktop,
agent or graphical installer.

The [initial seven-asset draft](evidence/H13-github-release-draft.md) was
prepared before licensing. GitHub's asset digests and full downloaded bytes
matched that candidate. Retargeting the draft, attaching the approved license
files and verifying the final asset set precede publication.

## Release checklist

1. Confirm the milestone gate, source commit, clean checkout and actual test
   evidence. Rehash the ISO, source archives, inventory and other intended assets.
2. Review original-project and component licenses, required notices, corresponding
   source availability, credentials and personal data. Publish no binary while
   the required owner license decision is open.
3. Use a tag pointing to the accepted source commit. Create a draft prerelease
   with exact scope, qualifications, VM/hardware results, versioned build/recovery
   instructions and SHA-256. Never label an interim ISO as the final installed
   desktop release.
4. Attach the exact media, corresponding-source bundle, component inventory and
   a release-specific SHA256SUMS listing only attached files. Keep raw logs local
   unless sanitized and separately reviewed.
5. Compare GitHub asset sizes and server-reported digests with local files. Fetch
   the assets through the release download route and run `sha256sum -c` before
   publishing. Then publish the reviewed draft and verify the public links.
6. Record the release URL, tag, artifact hashes, known limitations and publication
   result in repository evidence and regenerate the dashboard. Any later hotfix
   gets a new tag, artifacts and acceptance evidence; do not silently replace a
   tested immutable release.

Major Phase 2 previews may use prereleases after their own actual milestone
acceptance and the owner approval required before B01. A G2 release requires the
full installed-system and agentic gates. This is a delivery convention, not a
promise that an unbuilt feature has passed.

For the H13 source/build and testing instructions, use
[FOUNDATION-TESTING.md](FOUNDATION-TESTING.md),
[FRESH-BUILD.md](FRESH-BUILD.md), [RECOVERY.md](RECOVERY.md) and
[H13 evidence](evidence/H13.md). The complete local owner-testing export stays
outside Git under `.local/releases/toddy-foundation-2026-11-07/`.

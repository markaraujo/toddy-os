# ADR-0103: Use GitHub Releases for accepted delivery artifacts

- Date: 2026-11-07
- Status: Accepted for release preparation; public foundation publication blocked by D10

The Pages dashboard tracks development progress. A GitHub Release will hold each
large, accepted, immutable delivery with its tag, image, corresponding source,
component inventory, checksums, test summary and explicit limitations. The first
candidate is the H13 command-line foundation at commit
`e24e452399621607a8386db582e5776bd66994da`, with draft release tag name
`v0.1.0-foundation.1`. GitHub has not created the public Git tag for this draft.
At publication, verify that the created tag points to that exact commit. Later
documentation commits do not change the tested artifact.

Create a draft prerelease first, attach and verify candidate assets, then publish
only after the owner resolves D10's original-project code/documentation/artwork
license and the release review passes. A draft is a preparation checkpoint, not
a public download or G2 acceptance. Keep the local H13 export as the authoritative
evidence and preserve its original hashes. A release-specific checksum file lists
only assets actually attached to that release. Avoid uploading raw local test
workspaces or build logs without a separate data review; sanitized evidence is
already committed under `docs/evidence/`.

Future major deliveries use the same sequence after their own acceptance gates:
freeze the source commit and artifact hashes, validate the media in a disposable
VM, audit licenses/notices and credentials, make a draft, upload source and media,
verify GitHub's asset sizes/digests and download checksums, then publish. Label
previews as prereleases and describe missing functionality precisely. B01-B13
remain owner gated by ADR-0063; this delivery mechanism does not authorize their
implementation. The installed desktop/agent/installer release requires its G2
evidence, including actual blank-disk installation and post-install boot, before
being described as such. The public project-original license decision applies to
every publication.

GitHub documents draft creation before asset attachment and publication, and
limits each release asset to under 2 GiB. The measured ISO (1,095,000,064 bytes)
and corresponding-source tar (718,551,040 bytes) each fit. Sources consulted:
[Managing releases](https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository)
and [About releases](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases),
consulted 2026-11-07. If platform limits change, recheck them before upload.

Alternatives: Git alone cannot host the binary image in this repository; Pages is
intentionally limited to the dashboard. A second storage provider would create
unneeded account, synchronization and provenance work for the current artifact.
GitHub Releases keeps source revision, checksums and download location together.

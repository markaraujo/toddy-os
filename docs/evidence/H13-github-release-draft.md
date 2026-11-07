# H13 GitHub Release draft verification

The first large-delivery draft exists at
[`v0.1.0-foundation.1`](https://github.com/markaraujo/toddy-os/releases/tag/untagged-4fec1c479881718b4c29).
GitHub reports it as a draft prerelease, targeting the accepted H13 source commit
`e24e452399621607a8386db582e5776bd66994da`. The public Git tag is not yet
created; verify it points to that exact commit when the draft is published.

Seven assets are attached: the 1,095,000,064-byte ISO, the 718,551,040-byte
corresponding-source tar, the component inventory, source-input inventory, source
checksums, complete source-history bundle and a release-specific SHA256SUMS.
GitHub reported `uploaded` state, matching size and matching SHA-256 digest for
every asset. Every asset was also downloaded again through the draft release and
rehashed against that checksum file. The downloaded SHA256SUMS matched the local
release-specific file. See the [exact asset report](H13-github-release-draft.json).

The ISO hash remains
`4dd9de7a38c4f0d745c2fb74bfdb63e552c372211e5274961814fd9b3d7d22b9`.
The original local owner-testing export, including raw build/test logs, remains
outside Git. The public candidate includes sanitized committed evidence and
corresponding sources; raw local workspaces were not uploaded as release assets.

**The draft is not a public download.** D10 still requires the owner's decision
on licenses for original Toddy OS code, documentation and artwork before public
binary publication. The suggested terms in [LICENSING.md](../../LICENSING.md)
are MIT for original code and CC BY 4.0 for original documentation/artwork where
applicable; no owner approval of those terms has been inferred. Component terms
remain individual. The H13 owner-review boundary before B01 is separate and
unchanged. The draft can be published only after the license decision and the
final release checklist in [RELEASES.md](../RELEASES.md) pass.

The owner subsequently approved MIT for original code and CC BY 4.0 for
original documentation/artwork. ADR-0104 and the repository license files record
that later decision. This report preserves the draft's earlier seven-asset state;
the final published release requires a new tag/source and asset verification.

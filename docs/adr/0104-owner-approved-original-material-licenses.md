# ADR-0104: License original Toddy OS code and creative material

- Date: 2026-11-07
- Status: Accepted by explicit owner approval
- Resolves: D10

The owner approved MIT for original Toddy OS software code and Creative Commons
Attribution 4.0 International for original documentation and artwork. Their
separate terms apply only to material the owner can license. `LICENSE` contains
the MIT grant with an explicit original-code scope. `LICENSES/CC-BY-4.0.txt`
contains the official CC legal text; LICENSING.md states attribution and scope.
Original approved brand assets are marked in assets/brand/README.md.

The same release includes Linux, GNU and other upstream code and notices. Those
components retain their own licenses; the project does not relicense the whole
operating system under MIT or CC BY. Source archives, component/license inventory
and corresponding notices accompany the image. Model weights, voices and
optional firmware are separate future decisions. Copyright permission does not
settle trademark rights in the Toddy OS identity.

This approval removes the original-project license dependency for public
distribution of the tested foundation. It does not accept untested hardware,
change the H13 owner-review boundary before B01, or turn the command-line ISO
into a desktop/installer release. The GitHub draft must be retargeted to a source
revision containing these grants, and its source bundle/checksums verified before
publication. The original tested image SHA remains unchanged.

Sources consulted: official [SPDX MIT text](https://spdx.org/licenses/MIT.html)
and [Creative Commons BY 4.0 legal code](https://creativecommons.org/licenses/by/4.0/legalcode.en),
both accessed 2026-11-07. The unmodified upstream plain-text CC legal code was
retrieved from the official site with SHA-256
`9ba9550ad48438d0836ddab3da480b3b69ffa0aac7b7878b5a0039e7ab429411`.
The SPDX MIT text before replacing the copyright holder had SHA-256
`b05785f9f18e6716bab63424b11454513b9943a222595b70411009202fc592b5`.

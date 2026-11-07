# ADR-0099: Check runtime build paths at target-root boundaries

- Date: 2026-11-07
- Status: Regression checks passed; full native runtime retry pending

The third complete H10 generation passed ownership and whole-tree attribution,
then failed runtime availability with exactly 82 identical path findings. The
report resolved 791 dynamic executable entries and 373 executable scripts, with
no other findings. The rejected inputs were packaged Python fixtures, Linux
documentation and Vim helpers under nested directories named sources or tools.
The auditor mistakenly matched those names anywhere in an absolute pathname.

Reject the actual build roots /sources, /tools and /mnt/lfs and their descendants,
not similarly named directories within installed package trees. Check both the
requested path and its resolved in-image symlink target. Reject noncanonical
paths, double-leading slashes and traversal explicitly. Keep every ownership,
mode, hash, native loader and shebang check. This fixes the auditor rather than
waiving missing dependencies or deleting legitimate package files.

Alternatives: removing legitimate documentation/helper payloads would change
packages to accommodate an incorrect predicate; exempting entire packages would
conceal real failures. Precise root-relative path boundaries are already used by
the source inventory and the target-root resolver. Sources are the actual frozen
package manifests and failed 16-image-runtime-audit.json, plus the accepted
ADR-0074 native loader contract. No upstream version or release gate changes.

Focused regressions exercise owned nested paths, direct build roots, traversal,
noncanonical spelling and a /usr/bin alias into /tools. The failed original
assembly and report remain failed; any native rerun is separate evidence.

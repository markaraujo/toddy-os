# ADR-0097: Supply a temporary null device while generating the Info index

- Date: 2026-11-07
- Status: Native empty-device-tree regression passed; full assembly retry pending

The first complete live root passed source inventory, payload copy, fresh
directories/database/accounts, live configuration, service policy, console and
loader-cache stages. Native install-info then failed before indexing as.info:
`No such file or directory for /dev/null`. The failed root and all stage reports
are retained. The earlier component fixture included devices for its minimal
runtime, so it had not exercised this full-root boundary.

Frozen Texinfo 7.3 `install-info/install-info.c:2001` explicitly reopens stdin
on NULL_DEVICE before processing options. Preserve that upstream behavior.
During native index generation only, create a root-owned character device 1:3
with mode 0666 inside the protected image's physical /dev. Remove exactly the
created inode in a finally block, including command failure. Refuse redirected
parents, regular files, unexpected devices, owners or permissions. A valid
pre-existing null device in a private component fixture is verified and retained.
The full root still must pass its unchanged whole-tree attribution audit;
special device nodes are not allowed in its compressed package image.

Do not copy or bind-mount the builder's /dev, keep a host mount in the image,
patch install-info to ignore the error, or skip documentation generation.
Native boot supplies /dev through devtmpfs as already specified in live_init.sh.

The corrected native fixture starts without /dev/null, generates two identical
indexes, exercises actual Info readers/menu traversal and verifies cleanup.
Regular-file/symlink replacements are refused and a controlled exception removes
the temporary node. Installed package status and the original shared index are
unchanged. Probe exit 0; raw report SHA-256:
`e7a8ebfa047958c52b86b533cb7d2412e2cf31c2f96e1091340c7dadf72f6449`.
No complete-image or boot pass is inferred from this focused regression.

# H10 post-delete reconciliation

The actual H10 tree was removed after complete host tar/member/gzip verification.
The old guest state remains `root-retirement-intended-no-replay`: its final retained
media check used a 256MiB default, despite eligibility allowing 8GiB files. Three
large media files caused the postcheck to refuse after removal. Never replay that
retirement or rewrite its original state to complete.

First stage **only the new**
`scripts/build/phase2/h10_root_retirement_reconcile.py` at the matching fixed
`/opt/toddy-build/scripts/build/phase2/` path in the designated builder, owned by
root with mode0644. Verify its SHA against the committed source. Do not perform a
full source sync yet: the original producer and image namespace driver are pinned
by the old proof and must retain their exact bytes through this reconciliation.
The host source entry is:

```sh
python3 scripts/host/phase2_h10_root_retirement_reconcile.py
```

It uses the exact existing `.local/phase2/h10-expanded-root-custody-1` gzip,
raw metadata and immutable completed host receipt. It independently repeats full
member/ACL/xattr/symlink/hardlink/byte and decompression verification, then uses
the existing protected namespace driver with one fixed route added **in memory**.
The original driver/producers on disk remain unchanged. No request supplies code,
a path, a validator or a permission flag.

The fixed root helper requires the exact original retirement-intent SHA, original
producer/driver hashes, old completed host receipt, original raw metadata, absent
root, every preserved regular hash (8GiB bound), every preserved link identity and
raw target/xattrs, and actual positive free-space gain from the original
43430825984-byte measurement. The coordinator's independent observed after-value
was47213391872 bytes; the companion records its own current measurement honestly.
It never calls removal, replay or save on the old state. The new guest receipt is
`/var/log/toddy/phase2/h10-expanded-retirement-reconciled-1.json`; the new host
companion is `postcondition-reconciliation-1.json` within the existing custody
context. Preserve both old and new receipts. Existing companions fail closed.

Only after actual successful reconciliation may the coordinator sync the separate
future-H11 postcheck-bound fix and other reviewed source. That fix does not repair
or overwrite the H10 intent retroactively. This source/test change itself is not
an actual reconciliation result or acceptance claim.

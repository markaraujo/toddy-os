# Fixed export3 public asset transfer

After the sole guest coordinator finishes the actual fresh native export3,
run on the host while the owned candidate remains available:

```sh
python3 scripts/host/collect_package_export3.py
```

The entry accepts no paths/actions/credentials. It reuses the existing exact
receipt/hash/size/read-only tar-stream mechanism with only two enumerated
internal profiles. Export3 is fixed at
`/mnt/lfs/sources/stage/toddy-package-export-3`; its fresh host destination is
`.local/phase2/mvp-package-export-3/assets`. The separate private
`.local/phase2/mvp-package-export-3/verified.json` binds actual exported files,
archive receipt SHA and measured sizes. Every incoming regular member is
validated, rehashed, fsynced and never extracted with supplied permissions or
paths. The100GiB+512MiB host reserve plus actual transfer bytes remains required.

The guest operation is read-only and copies only exact unsigned public assets.
It does not sign, download, publish, install or change guest state. Existing
host destination refuses replay. Only after actual transfer verification does
the authorized host signer create export3 signatures over these exact bytes;
return those public signatures to the same native export3 for independent native
verification and image preparation. Private signing material never enters the VM.
The completed unsigned transfer alone proves no signature or runtime acceptance.

The original `collect_package_export2.py` CLI keeps its export2 source and host
destination unchanged. Both export2 bytes and any retained export2 signatures
remain immutable; export3 never writes, replaces or falls back to them. Existing
signatures at an unsigned source cause exact-namespace refusal rather than being
silently dropped or copied as a new native signature proof.

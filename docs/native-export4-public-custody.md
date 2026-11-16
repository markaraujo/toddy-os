# Fixed export4 transfer and public signatures

After actual installer5 version3 and MVP projection2 pass, the sole guest
coordinator creates the fresh unsigned `toddy-package-export-4`. Earlier
exports2/3, signatures, intents and actual verification receipts remain immutable.
Run this fixed read-only host collector while the owned candidate is available:

```sh
python3 scripts/host/collect_package_export4.py
```

The entry accepts no paths/actions. It reuses the exact native receipt/flat
namespace/size/hash/tar-member/fsync mechanism and existing100GiB+512MiB host
reserve, writing only fresh `.local/phase2/mvp-package-export-4/assets` and its
private `verified.json`. Collector2 and collector3 defaults are unchanged; the
internal enum now admits only explicit generations2,3,4.

The parent signer separately signs that exact new public Release and verifies
both public signatures/cleartext with the independently approved certificate.
Retain `.local/phase2/mvp-package-export-4/signed.json` with exactly:

```json
{
  "state": "signed-publicly-verified-export4",
  "signatures": {"Release.gpg": "ACTUAL_SHA256", "InRelease": "ACTUAL_SHA256"},
  "published": false
}
```

The placeholders describe required actual hashes, not a generated success file.
Do not copy a signer home/key or reuse export3 signature bytes/receipts. After
actual signing and verification, run:

```sh
python3 scripts/host/stage_package_export4_signatures.py
```

Only two bounded public signature bodies and public custody hashes are sent via
fixed `image_native.sh signatures-export4`. Host transfer/signature/Release/key
pins are independently checked first. The native producer uses the already
measured GnuPG stream contract: InRelease on stdin, `--output -`, status on fd2;
approved `VALIDSIG` is checked separately and actual stdout must equal the exact
export4 Release. Detached verification is actual native `gpgv` too. All original
root-owned protected-stage, global lease/FD8, public-only temporary HOME, exact
native executable ownership, no-overwrite, readback, fsync and cleanup guards
remain mandatory. No export3 failed intent is required or reinterpreted.

Fresh paths are:

- native `/mnt/lfs/sources/stage/toddy-package-export-4/{Release.gpg,InRelease}`
- native `/var/log/toddy/phase2/package-export4-public-signatures-1.json`
- temporary `/mnt/lfs/run/toddy-export4-public-verification-1`
- host `.local/phase2/mvp-package-export-4/native-signatures-verified.json`

Success is packet-bound `native-public-signatures-verified`,
`export_generation:4`, `signature_attempt:1`, both actual native verification
exits0, exact cleartext/readback and temporary cleanup. Existing/partial outputs
refuse replay. Helpers3 and their default source/destination/packet semantics
remain unchanged. This source glue does not execute signing, publish artifacts,
include private keys or claim installer/OS acceptance.

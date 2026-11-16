# Fixed export5 public custody

After actual coherent installer6/version4 and fresh MVP projection3 succeed,
create a NEW native `toddy-package-export-5`. Preserve all earlier exports,
packages, signatures, intents and receipts. Host actions accept no arbitrary
source/destination/signing-context arguments:

```sh
python3 scripts/host/collect_package_export5.py
# Parent signs/verifies the exact new public Release separately.
python3 scripts/host/stage_package_export5_signatures.py
```

The collector uses only `/mnt/lfs/sources/stage/toddy-package-export-5` and fresh
`.local/phase2/mvp-package-export-5/assets`, retaining exact unsigned receipt,
file/hash/size, read-only tar, fsync and host reserve checks. The original
collector2 default remains2; later enum members are only3,4,5, never arbitrary
paths. Shared host signature packet helpers admit only3/4/5; all previous CLI
defaults stay unchanged.

Before public-signature return, actual host signing/verification must produce
`mvp-package-export-5/signed.json` with
`state:signed-publicly-verified-export5`, exact `Release.gpg`/`InRelease` signature
hashes and `published:false`. The helper independently rechecks approved public
key, transfer receipt, actual Release, signatures and InRelease cleartext.
Only those two bounded public signature bodies and custody hashes enter the VM.
No signer home, private key, owner credential or new signing decision is carried.

The fixed `image_native.sh signatures-export5` entry retains the global lease
FD9, original input FD8 and protected-stage view. Fresh native paths are:

- `/mnt/lfs/sources/stage/toddy-package-export-5/{Release.gpg,InRelease}`
- `/var/log/toddy/phase2/package-export5-public-signatures-1.json`
- temporary `/mnt/lfs/run/toddy-export5-public-verification-1`
- host `.local/phase2/mvp-package-export-5/native-signatures-verified.json`

Actual native `gpgv` checks both signatures and the approved fingerprint.
InRelease uses the already qualified stream contract: stdin signed public data,
`--output -`, status fd2 and exact stdout comparison to current export5 Release.
Source-owned native verifier, protected public-only HOME, no-overwrite,
unchanged source bytes, copied hash/fsync and cleanup checks remain mandatory.
There is no dependency on any failed export3 intent. Completion requires actual
packet-bound `native-public-signatures-verified`, `export_generation:5`,
`signature_attempt:1`, both native exits0, exact cleartext/readback and temporary
cleanup. Existing/partial output refuses replay; no earlier generation is
reinterpreted or overwritten. This source change proves no actual signing,
publication, installer or boot acceptance by itself.

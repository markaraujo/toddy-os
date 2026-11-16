# Export3 public signature reconciliation2

The first native signature staging reached two successful cryptographic `gpgv`
verifications, then failed because its expected `clear` file did not exist. Its
receipt remains `public-signature3-staging-intended-no-replay`; no signature was
copied. Preserve that intent and actual error evidence. Do not rerun attempt1,
remove its receipt or label its partial verification as completed staging.

A separate actual read-only probe of native GnuPG2.5.24 demonstrated this contract:

```text
gpgv --status-fd 2 --output - -
```

With the exact public InRelease on stdin and approved guest keyring, exit0
returned480 stdout bytes with SHA256
`b8af6924da4a2da3db83abc337e1a131daf8c85e5507689762c3ca7109f1d8c2`,
identical to the actual Release, while approved `VALIDSIG` was on stderr.
The retained coordinator evidence is
`.local/phase2/mvp-native-gpgv-stream-probe-1.json`. Frozen upstream GnuPG2.5.24
`g10/gpgv.c:239` accepts output selection and `g10/mainproc.c:1108-1113` describes
signed plaintext output; the new producer relies on the measured stream behavior
and never assumes filename creation proves verified cleartext.

After committed helper sync, the sole coordinator uses this NEW fixed host entry:

```sh
python3 scripts/host/stage_package_export3_signatures_reconcile2.py
```

It rebuilds/rechecks the same actual approved public packet, then invokes only
`image_native.sh signatures-export3-reconcile2` in the existing protected source
view with the original packet FD8 and canonical global lease FD9. The new native
producer verifies the preserved attempt1 state, exact original packet/host
receipt/public source hashes, unchanged native verifier and absence of public
signatures, old temporary directory and ambiguous old `.part`. It refuses an
already successful, unrelated or uncertain previous state.

New paths are:

- `/var/log/toddy/phase2/package-export3-public-signatures-2.json`
- `/mnt/lfs/run/toddy-export3-public-verification-2`
- host `.local/phase2/mvp-package-export-3/native-signatures-verified-2.json`

The original helper/source and intent1 remain unchanged. Reconciliation2 reuses
its fixed guard/custody/copy/fsync checks, but routes only the InRelease
verification through actual native `--output - --status-fd 2 -`. It verifies the
approved fingerprint separately on stderr, requires stdout to equal the exact
guest Release, and retains only those measured public clear bytes in its private
temporary directory for the existing readback check. Detached signature
verification remains actual native `gpgv` as before. No signature copy happens
until both verifications and exact cleartext comparison pass.

Every new intent/result links the unchanged previous intent SHA and explicitly
records `previous_attempt_claimed_success:false`. Successful completion requires
actual signature copies/readback, unchanged inputs and cleaned public-only HOME.
New partial paths or receipts refuse replay. No private material, signer context,
new key, archive replacement, publication or old success is introduced.

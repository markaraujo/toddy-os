# Return export3 public signatures only

After actual export3 transfer, parent-controlled signing and host verification,
retain `.local/phase2/mvp-package-export-3/signed.json` with
`state=signed-publicly-verified-export3`, exact `signatures` hashes for
`Release.gpg` and `InRelease`, and `published:false`. Commit/sync the fixed helper
sources, then the sole coordinator runs on the host:

```sh
python3 scripts/host/stage_package_export3_signatures.py
```

There are no source/destination/signing-context arguments. The host rechecks the
actual export3 transfer receipt, current Release/public-key/export bytes, approved
independent public certificate pin, both actual `gpgv` exits/fingerprint and exact
InRelease cleartext. It sends only the two bounded public signature bodies plus
public custody hashes. It reads no signer home, private key or unrelated context.

The fixed `image_native.sh signatures-export3` action preserves original input
FD8, the canonical inherited global lease FD9 and private protected-stage view.
The builder helper guards the target again, requires root-owned protected exact
export3 namespace, matching guest Release/export/public key and fresh signature,
intent and temporary paths. No export2 or existing signature is overwritten.
It validates the source-owned installed native `gpgv`, then invokes it through
`/usr/sbin/chroot /mnt/lfs` for both detached and clear signatures with the pinned
fingerprint, private public-only HOME/keyring and exact guest Release. It checks
cleartext equality before copying/fsyncing the exact signatures and confirming
unchanged source inputs. The temporary public verification home is removed
before a successful receipt is published.

Native custody is retained at
`/var/log/toddy/phase2/package-export3-public-signatures-1.json`; the host preserves
its actual packet-bound result in
`.local/phase2/mvp-package-export-3/native-signatures-verified.json`. Only
`state=native-public-signatures-verified`, both native exits0 and actual temporary
cleanup mean completion. An existing/partial intent, destination or result refuses
replay and requires outcome inspection. Signing/publication and OS acceptance
remain separate actions; this helper creates neither keys nor signature claims.

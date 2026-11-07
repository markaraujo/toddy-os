# ADR-0080: Audit fresh image identity independently of file attribution

- Date: 2026-11-07
- Status: Private native verification passed; full image and boot pending
- Extends: ADR-0055, ADR-0065, ADR-0072 and ADR-0073

The foundation distribution must not inherit the builder's authentication or
machine state. Exact native package attribution proves where bytes came from;
it does not authorize those bytes as redistributable credentials. A future
package or explicit generated-file declaration could otherwise account for an
authentication file while leaving that separate release requirement untested.

Add a read-only image_identity audit to both gated assembler profiles after
payload, attribution and runtime checks. Require the seven generated account
files to match the reviewed 15-user/35-group baseline exactly, including empty
machine-id/sub-ID files, locked credentials, numeric ownership, permissions,
absence of extended attributes and a single hardlink. The existing canonical
root-owned DBus link to /etc/machine-id is allowed without dereferencing it.
A DBus identity value is forbidden. This does not change account generation.

Require empty root/home and known authentication directories when present:
APT auth.conf.d, TLS private storage, system and encrypted Systemd credential
stores, and network authentication state. Require absence of account backups,
APT auth.conf, Systemd credential.secret/random seed/entropy state and cloud
initialization state. Reject generated SSH host identities. This policy is for
the fresh foundation distribution, not an installed user's persistent system.
Directories for future desktop services are preventative boundaries, not proof
that those services are installed or tested.

Inspect physical ancestors and filesystem identity before reading any policy
path. Never follow symlinks, read special nodes, traverse private child data or
export unexpected bytes, content hashes, extended-attribute values or child
names. Findings contain only the fixed policy path and reason. Refuse unexpected
state and preserve it for private diagnosis; do not silently sanitize a stage.
The assembly caller retains its exclusive lock and private-generation policy.

Alternatives: trusting attribution alone conflates provenance with credential
approval; extending the PEM scanner to arbitrary passwords cannot recognize
all secrets; copying and deleting builder authentication state imports secrets
before attempting cleanup. Independent fresh-state constraints complement the
existing allowlisted payload and exact documentation-marker review. They do
not replace full image/configuration inspection, source/license inventory or
first-boot identity verification. The report explicitly keeps whole-image
credential acceptance false.

## Frozen sources

- LFS 13.1-systemd section 7.6, chapter07/createfiles.html, SHA-256
  f042fcc6b3389673a39fbc7c99eaca8b2589fce453d87c5b01366408af3d0867;
  exact account baseline and service extension remain in config/live-account-baseline.json.
- Systemd 261.2 man/machine-id.xml, SHA-256
  8107d7f898dbcac50b03a48de9cbae46d9b9ee4835ebf660f7678ee5c3204b68:
  reusable images should carry no machine-specific identity. An empty file
  permits runtime binding but does not itself trigger first-boot semantics.
- Systemd 261.2 man/systemd.exec.xml, SHA-256
  d2cba4d37f262dc0ce090a193b64dc3065aad14cba6beb925dbbc958110fd67a:
  system credential search paths include etc/run/usr/lib credstore and their
  encrypted counterparts. Encryption does not authorize redistribution.
- Systemd 261.2 man/systemd-creds.xml, SHA-256
  021074d8e2e3b10e3b78e06eab5676b6fb9ef6d9b9ad6d8e5587674d59f00cb4,
  identifies the host credential.secret key.
- Systemd 261.2 man/systemd-random-seed.service.xml, SHA-256
  f11753aa942edf3fc4ed320dc611fb8c975374dc6d661ec990c5ee66426efa42,
  requires care with cloned random seeds and recommends removing them from
  images replicated to multiple systems.
- APT 3.0.4 doc/apt_auth.conf.5.xml, SHA-256
  8abba265dc159c58dfa343e3c4040f276d551546006eeff3a4178a55cc8390fd,
  identifies auth.conf and auth.conf.d as login/password storage.

These files were inspected directly in the frozen local source archives.

## Verification and recovery

Reproduce the private native integration experiment with
`python3 scripts/host/probe_image_key_marker_review.py --identity`.
It installs only copied, hash-verified own packages into a new temporary root,
uses the same fresh account and attribution components, and leaves the installed
build target unchanged. Complete raw reports remain content-addressed in
.local/logs/h11-image-key-marker-review-<sha256>.log. Successful temporary roots
are removed; failed generations are preserved.

The first attempt reached the new DBus negative case but assumed this minimal
OpenSSL package closure included DBus. It does not. Preserve failed fixture
/mnt/lfs/tmp/toddy-key-marker-review-_eh0fnnt and report SHA-256
79b18d9242c6e973b72c55d5c41789718b5563a43881729321da8c1fd629cd08.
Correct the fixture by explicitly adding and positively checking the documented
canonical alias before replacing it with identity bytes. No production policy,
package dependency or acceptance assertion is relaxed.

The corrected complete probe passed with eleven real native packages, seven
fresh account files, 15 users and 35 groups. Eighteen negative cases reject
explicitly declared APT authentication, credential.secret, random seed, account
backup, root/user SSH/netrc state, APT/TLS/encrypted-store contents, SSH host key,
changed same-length account bytes, mode, extended attributes, machine ID, DBus
identity bytes, outside symlink, FIFO and an external hardlink. The declared
APT file first passed attribution and then failed this independent policy.
The outside sentinel remained unchanged and the restored fresh image passed.

Complete successful report SHA-256:
bba61825fe13dbdf1d3aa01afb8a2bdabd7ed90ed50d229ce7d9b1ce77446e12.
Verified image_identity.py SHA-256:
e6649b138c3188056107bccacbbd6188e4c7f6525c7a64c9efa5b0abe1b0d219.
Native Dpkg status stayed unchanged at SHA-256
96ce580273ad5ce7f97557905f2be3ae918ee8e6da29ef7167788720b99c6f4e.
The same run retained the six qualified documentation findings and passed all
nine marker, ten owned-payload and ten attribution negative cases. This run
did not repeat the separate runtime-loader experiment. Successful fixture
/mnt/lfs/tmp/toddy-key-marker-review-qycmvn2w was removed after recording results.

No running Berkeley source, installed package, account, global build input or
physical disk was changed. H07 remains active; H10/H11 production gates remain
closed. Full assembled-image credential inspection and actual fresh boot identity
are still required before G1. This component supplies no package/milestone marker.

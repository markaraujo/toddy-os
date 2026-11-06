# ADR-0021: Freeze public TLS trust data for native build clients

- Status: Accepted; native package and TLS checks pending
- Date: 2026-11-06
- Scope: H07 supplemental dependencies; H08/runtime trust must be auditable

## Decision and evidence

Use curl's dated Mozilla CA conversion cacert-2026-11-05.pem as an explicit
source-data component, not workstation trust files. The official dated PEM and
published SHA-256 agree:
427c064216761a1e72a8b30f0d954d08cb6e4435a82091fb865afd20c8497285.
It contains 118 certificates and 200116 bytes. Freeze the dated URL and digest
in supplemental-sources.lock.json; verify again before packaging. Preserve the
Mozilla MPL-2.0 notice and complete official license text. HTTPS/publisher SHA
is the stated trust basis; no separate cryptographic signature is claimed.

Install a native ca-certificates package with /etc/ssl/certs/ca-certificates.crt
and compatibility symlinks for OpenSSL/Python clients. Hash/link/certificate
parsing checks precede actual native Curl verified-HTTPS and negative certificate
checks. No private/local workstation CA or provider credential is copied.

This bounded initial trust package avoids introducing p11-kit/make-ca before
its additional BLFS dependencies exist. A later NSS/p11-kit desktop integration
must share an explicitly reviewed trust source and retain Mozilla constraints;
the PEM conversion does not carry every Firefox name/domain constraint. No
claim of Firefox-equivalent policy follows from installing PEM roots.

Vim's full downloader tests require native network tooling. Keep their tests
unchanged and build the independent MarkupSafe/Jinja2/service/filesystem chain
first, then required native supplemental TLS/client dependencies, then Vim.
This changes scheduling only; Vim acceptance and final H07 closure remain
mandatory. No runtime hosted provider is introduced.

## Alternatives and consequences

Copying host roots would import unrelated workstation policy and damage
reproducibility. An unpinned current URL would vary between builds. Disabling
TLS verification is rejected. BLFS make-ca is a valid later integration, but
its dependencies and generated trust inventory must be built and tested first.
The dated snapshot is a deliberate package update boundary; it does not claim
automatic trust updates. Future trust updates require a new verified package.

## Primary sources

- [curl Mozilla CA conversion and policy](https://curl.se/docs/caextract.html).
- [Dated Mozilla-derived PEM](https://curl.se/ca/cacert-2026-11-05.pem) and
  [publisher SHA-256](https://curl.se/ca/cacert-2026-11-05.pem.sha256).
- [Official MPL-2.0 text](https://www.mozilla.org/media/MPL/2.0/index.815ca599c9df.txt),
  SHA-256 fab3dd6bdab226f1c08630b1dd917e11fcb4ec5e1e020e2c16f83a0a13863e85.
- Frozen BLFS 13.1-systemd make-ca/Curl pages and current source archives.


Initial native Curl profile explicitly uses OpenSSL, the frozen CA bundle and
Nghttp2; cookie support is disabled together with absent Libpsl. These build
clients need verified downloads/HTTP APIs, not cookie sessions. Do not claim
public-suffix cookie filtering or features absent from curl --version. The
browser's later cookie/PSL requirements must be independently built/tested.

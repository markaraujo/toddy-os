# ADR-0118: Private explicit resumable public artifact acquisition

Date: 2026-11-08 UTC. Status: accepted.

B03 uses a standard-library acquisition boundary driven only by a trusted pinned
catalog and explicit artifact hash/license/network consent. Imports/model output
cannot grant egress. The UI/installer can reuse this headless client in B06/B12;
credential storage and atomic backend activation remain B05.

An owned0700 cache,0600 regular single-link files, exclusive flock and actual-byte
rehash protect partial state. Exact expected length and SHA256 are mandatory before
an atomic no-replace publication. Range mismatch fails; a200 ignoring Range safely
restarts only the owned partial. ETag does not authenticate bytes and is not trusted.
Corrupted bytes remain unactivated until explicit inspect/remove. No automatic
retry, proxy credentials or implicit download. TLS remains verified; redirects stay
HTTPS and forward no credentials. GGUF data is never extracted/executed here.

Local acquisition gates the pinned AVX2 flags,8GiB total/4GiB currently available
memory and artifact+1GiB free space. Model inference remains4threads/8GiB AS cap.
Remote spend defaults off; API setup holds references and fixture-only availability,
with no invented cost estimate. Deferred mode preserves independent offline base.

Native evidence: acquisition-3 ten file/TLS-loopback tests, acquisition-cli-1 choices;
B03-native-local-tool proves the separate real full model/task. No paid/live API
or actual public resumable1.8GB transfer is claimed. A blocked network read can take
up to30seconds before cancellation; later UI must display pending cancellation.

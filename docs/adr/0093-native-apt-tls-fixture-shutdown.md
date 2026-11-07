# ADR-0093: Complete TLS shutdown in the native APT test server

- Date: 2026-11-07
- Status: Accepted after actual native HTTPS and package integration passed
- Scope: Disposable HTTPS fixture, frozen Python 3.14.10 / OpenSSL 4.0.3 / APT 3.0.4

The actual installed APT passed file-repository dependency installation,
upgrade/conffile preservation, signature/key/index/payload rejection and
remove/purge, then rejected the fixture's HTTPS response with unexpected TLS
EOF. The temporary server had wrapped ThreadingHTTPServer's socket in TLS but
inherited socketserver.TCPServer.shutdown_request, which performs plain TCP
shutdown(SHUT_WR). Frozen Python Lib/socketserver.py confirms this behavior;
Lib/ssl.py SSLSocket.unwrap calls the TLS object's shutdown operation.

Override only the disposable server's shutdown_request to unwrap/complete TLS
before shutting down the returned TCP socket. Bound peer shutdown to two seconds
and close on peer errors. Preserve APT/OpenSSL verification and certificate/name
checks; do not enable ignore-unexpected-EOF or disable TLS security. Also create
the fixture's empty preferences.d to remove unrelated absent-directory warnings.

Alternatives rejected: ignoring EOF globally would weaken the client and mask a
fixture defect; dropping HTTPS tests would remove a required acceptance scenario;
recompiling already successful APT would not correct the server's shutdown.

The original actual postcheck exit 100 and log are preserved. Log SHA-256:
b5eae38a42706625edb7a5224b91d3d6d40409d86beee4dcfac39a14cefda1c3.
The native APT archive is already installed but unaccepted pending postchecks.
The recovery recipe verifies its complete installed payload and archive against
its own native provenance, saves previous reports and reruns all 142 unit tests
and all existing repository/HTTPS/cache checks through the guarded dispatcher.
No package rebuild/reinstall or blanket test waiver is needed.

## Actual verification

The corrected server passed trusted HTTPS retrieval and package installation.
Untrusted CA and wrong host name both returned the required exit 100; observed
acquisition worker ran as _apt UID 999/GID 998, with zero effective capabilities,
NoNewPrivs 1, seccomp mode 2 and one added filter. All 142 unit tests and the full
existing signed-repository/package/cache scenarios passed. The guarded recovery
step ended recipe/postcheck 0/0 with zero installed payload changes; no rebuild
was needed. See docs/evidence/H07-focused-apt.json for report hashes.

A separate retry exposed an existing version-check pipeline SIGPIPE (head under
pipefail); replacing head with a fully consuming sed filter preserved the same
assertion and removed the race. That actual 141 failure remains in history.

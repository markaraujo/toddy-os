# ADR-0166 — Owned HTTP runtime for the GNOME dependency closure

Status: selected profile; native results are linked below. Date: 2026-11-09.

Use frozen BLFS13.1-systemd basicnet/libsoup3.html/libsoup3.6.6 with the
independently owned GLib2.88.3/GnuTLS3.8.13/GLib-networking2.80.1,
libpsl0.23.3/ICU78.3 and nghttp2 security overlay1.71.0. No frozen-foundation
upgrade or alternate TLS engine. Preserve actual TLS availability checking;
enable introspection, original tests and PKCS11 fixture tests. Omit optional
GSSAPI/external NTLM/Brotli/Vala/docs/profiling/Autobahn/fuzz campaigns from this
minimal profile, without advertising their functionality. Internal NTLM parsing
remains independently testable; a missing external helper is not a passing test.

Review the exact source NEWS rather than assuming a version number proves
security:3.6.6 includes websocket bounds, header/value/duplicate-Host validation,
Content-Length/Transfer-Encoding ambiguity handling, range and multipart fixes;
3.6.5 includes stripping authentication on cross-origin redirects. Original
parser/header/range/cookie/redirect/HTTP2/TLS checks remain required. This records
the frozen source review, not a claim about future advisories or final-release
security acceptance.

Expose the same qualified public trust data as the GLib networking consumer,
read-only and only for the exact libsoup input. Keep source/usr/configuration
read-only, UID101/no capabilities/NNP and private loopback without external route.
Do not expose owner SSL private/configuration paths or introduce an external
compiler networking exception. Actual native TLS provider check passed at setup.

All35 enabled original drivers passed. Preserve22 nested skips:13 require absent
Apache, eight require unavailable ntlm_auth and one is upstream's timing/ASAN
conditional. Three additional Apache-dependent top-level programs were not built;
no Apache/auth/proxy/Autobahn matrix acceptance.246 original ELFs retained. The
actual C public-API consumer runs a loopback HTTP server and client on separate
contexts, checks exact response/status, rejects a pre-cancelled request before
server dispatch and recovers across two sessions. Four actual server requests
prove cancelled requests were not replayed/dispatched. No owner credentials,
external hosts or configuration are used. Timeout is a failure, not success.

Promote the qualified stage through the existing full-root measured native
transaction; verify actual installed library linkage/version and repeat only
that directly affected native C/SDK consumer. Do not rerun the unchanged original
suite. Package/archive, runtime closure and exact source/legal provenance remain
owned. An installed package with failed postcheck requires inspection and
verify-only recovery, never an uncertain reinstall. Actual GNOME/browser/native
network and physical validation remain separate B02 gates.

Native install/post0/0 changed133paths/281owned entries. Actual installed HTTP client/server, pre-cancelled refusal/no server dispatch/recovery and SDK passed with the same retained consumer bytes and no original-suite replay. [Proof](../evidence/B02-libsoup-install.json).

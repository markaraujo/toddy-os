# ADR-0165 — GNOME proxy and GLib networking profile

Status: accepted profile; runtime qualification is scoped below.
Date: 2026-11-09.

Frozen BLFS13.1-systemd general/libproxy.html selects libproxy0.5.12
(source SHA a1fa55991998b80a567450a9e84382421a7176a84446c95caaa8b72cf09fa86f).
Use its environment/GNOME/sysconfig/portal configuration support, owned Duktape2.7
PAC runner and existing curl8.23.0. Duktape bytecode loading/dumping remain
disabled in its independently owned package; this consumer evaluates PAC source.
Enable original tests and introspection; omit Vala/docs and unrelated KDE/macOS/
Windows configuration backends via supported switches. Do not introduce another
JavaScript runtime or claim a portal/proxy service works merely from compilation.

All five enabled original drivers passed, including actual private-loopback PAC
server, Duktape and GNOME memory-backend fixtures.29ELFs retained. Owned native
install/post0/0 changed23paths with29package entries; actual installed public API,
frontend/backend linkage, SDK and boxed-copy lifetime passed. The public API
explicitly returns direct:// for a malformed target URI: verify that safe fallback
and subsequent normal calls, not an invented NULL/error contract. Tests use
synthetic proxy settings in private processes, no user settings or owner secrets.
Remote proxy/PAC/WPAD and native GNOME interaction remain separate gates.

For GLib-networking2.80.1 keep upstream GnuTLS enabled/OpenSSL disabled, matching
its meson_options.txt guidance for general Linux. Enable libproxy and GNOME proxy
support; the environment backend is explicitly intended when libproxy is absent.
Keep installed test/debug payload off. The enabled original drivers cover both
proxy backends, certificates, database and default TLS/TLS1.2 local connections.
DTLS is disabled by upstream and is not a passing test or promised feature.

The first compilation succeeded; proxy drivers and29certificate cases passed.
Three original TLS programs aborted before cases because isolated synthetic /etc
omitted the actual newly installed factory roots. Fix the exact consumer profile
by exposing only qualified public /etc/pki/anchors and /etc/ssl/certs read-only,
plus its existing public bundle alias. Do not expose SSL configurations/private
keys, general /etc, write authority or an external route. Preserve all original
failures/passes and compiled binaries. Run only the three affected programs,
without rebuilding or replaying the approved proxy/certificate programs.

A stage-local GIO module cache is not the installed shared DConf/GIO resource.
Native ownership promotion must preserve its prior input/hash, regenerate from
qualified module inputs, update the tracked generated resource and check actual
installed TLS and DConf GSettings persistence. No ad hoc cache overwrite or
GNOME/browser acceptance from a standalone module probe. Subsequent verified
outcomes belong in the evidence index and continuation card.

[Owned proxy runtime](../evidence/B02-libproxy-install.json).

## Verified native GLib networking result

Only the three affected original TLS drivers were repeated; all passed, including
TLS1.2 and default TLS local connections. The first own C consumer used an
OpenSSL-specific BEGIN TRUSTED CERTIFICATE file which GIO does not parse.
Correct only that consumer: use the actual standard PEM bundle, enumerate121
roots, select public ISRG Root X1 and verify against the default database.
Consumer-only3 passed;38original ELFs and all staged files unchanged. Preserve
initial failures, no suite/stage replay.

Controlled ownership install/post0/0 changed90paths with240package entries. Omit
the compiler-local GIO cache from the archive. Verify the old tracked DConf cache
and module, generate the union for four owned modules, and update only its
tracked generated-resource metadata. DConf archive/module remain unchanged.
Actual installed default GIO/GnuTLS/root/malformed-certificate refusal/recovery
passed without module/TLS overrides; directly affected installed DConf GSettings
private-database persistence/new-bus/reset passed. No real user settings changed.
Local trust updates/recovery, remote DNS/TLS, native desktop and fresh combined
recipe qualification remain pending. [Proof](../evidence/B02-glib-networking-install.json).

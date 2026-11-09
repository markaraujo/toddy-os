# ADR0159: GNOME Keyring's frozen Gcr3 C ABI alongside Gcr4

Status: libsecret and co-installable Gcr3 owned, 2026-11-09.

GNOME Keyring50.0 source meson.build requires gck-1 and gcr-base-3. GNOME Shell
requires Gcr4/Gck2. The approved frozen graph already selects both book pages:
Gcr3.41.2 gnome/gcr.html SHAed85dac3bfba37b74ccd4a0e3d71f19425db398b9058b10fd18a5b8c0c8191a4,
Gcr4.4.0.1 gnome/gcr4.html SHA822f7cdc78943b463652ac63fd615fa3cca98e1acf9536f985af9f3d3bbe12ca.
Add co-installable versioned gcr3 native package; preserve existing Gcr4 and
foundation. This corrects the actual dependency slice, not the approved architecture.
Existing Keyring50source already matched official frozen cryptographic digest;
book-fetch helper refused to replace its richer initial root metadata. Reuse it,
never replace source identity or download/replan the foundation.

Build Gcr3 C/GTK3 libraries with supported introspection=false (legacy GIR implies
unneeded Vala generation), gtk=true, gtk_doc=false, ssh_agent=false. Main Shell
continues to use Gcr4 GI. Legacy GTK3 original UI programs require actual native
display and remain pending, never counted as portable passes. Core egg/Gck/Gcr
original programs, real encrypted transport/refusal/recovery and source/SDK
integrity are selected for this slice. Reuse exact qualified private keygen SDK,
119original cases, never install it or advertise a client/agent/server feature.
The sole encrypted public source sample uses the already qualified byte-identical
private writable clone; source stays unchanged/read-only elsewhere.

Initial Gcr3 setup aborted before library compilation: with ssh_agent=false,
meson.build still calls path() on not-found optional ssh-add/ssh-agent. Frozen
Gcr4 already guards those lookups with the same feature flag. Apply exact one-file
build-only correction to honor the declared disabled feature: empty unused path
variables and mandatory real program queries only inside the enabled branch.
No C/crypto/API/active-feature behavior, version or security policy change.
Patch/source hashes in gcr3-patches.lock.json. Preserve original failed setup and
source; new authenticated copy differs only meson.build, new work directory.
No unknown-state replay or fake executable. Source license/patch notice must be
included in owned promotion. Current libgcrypt/GnuPG overlay remains unchanged.

libsecret0.21.7 owned after22original programs/no nested skips,69ELFs retained,
staged/installed binary-value/schema/type refusal/two lifecycle cycles and GI/SDK/
audit0. No PAM/TPM module enabled, no real credentials used. This does not replace
actual Keyring backend/PAM/native graphical integration.
[libsecret evidence](../evidence/B02-libsecret-install.json).

Gcr3 patched input passed all43registered original core programs without nested
skips; no automated UI programs are registered by this profile. Actual installed
C transport/refusal/state-preservation/two recovery cycles and SDK/APT passed.
All339existing Gcr4 payload entries and its package archive stayed unchanged.
Install/post0/0 changed219root paths. No forced ownership overlap or fake optional
helper. Shared PGP schema cache and actual GTK3/GNOME UI remain pending.
[Gcr3 evidence](../evidence/B02-gcr3-install.json).

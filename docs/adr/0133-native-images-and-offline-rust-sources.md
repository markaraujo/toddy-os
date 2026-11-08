# ADR-0133: Native image primitives and frozen Rust source acquisition

- Date: 2026-11-08
- Status: Accepted; native Pixbuf qualified, Rust dependency sources verified

The first GdkPixbuf2.44.7 profile builds PNG/JPEG/GIF into the library, enables
introspection/thumbnailer and leaves optional Glycin/TIFF/weakly maintained other
loaders unqualified. SVG still requires actual librsvg loader integration. Keep
the native generated empty external-loader cache in staging: upstream DESTDIR
explicitly suppresses global cache writes. Assert comments-only contents and no
temporary paths, own the cache and verify it after installation. Later external
loaders require a controlled cache transaction and affected image checks.

Actual23 registered tests, native PNG/JPEG stream roundtrip, malformed-image
refusal and builtin format registry passed. Owned native install/post0/0 in
55.229s; actual Python GI PNG encode/decode/pixel check and cache hash passed.
This proves image/GI APIs, not a GTK window or desktop interaction.

Librsvg2.62.3 needs cargo-c0.10.24. The frozen cargo-c GitHub archive omits
Cargo.lock. Use only the published0.10.24+cargo-0.98.0 crate's lock as a supplement,
not a replacement or upgraded source. Official registry checksum
e033742583695968c690582ab678f65c133779767940c9bc35718e990a235d45 matched. Published
VCS and frozen GitHub tar both identify d7d1743e8d94faa858b4326e7d45e201f4347b27;
Cargo.toml.orig and all12 published Rust source files equal the primary archive.
The supplemental lock SHA is d7cd5b83a35fb486298c29d7a685d4bbb3b46e2454f93aaff5bc213369fde8a5.
Librsvg's own authenticated Cargo.lock is retained unchanged.

Acquire sources before the network-isolated native compiler. Reuse the already
authenticated official Rust1.96 bootstrap seeds privately for Cargo vendor only;
native product compilation remains the owned Rust1.97.1 SDK. No host/global tool
installation. A wrapper permits only rustc metadata/version requests and refuses
host source compilation. Private HOME/CARGO_HOME and explicit public sparse
registry avoid personal credentials/config; lock entries cannot authorize another
registry/Git URL or unsafe path. Cargo retry budget is one unchanged transient
retry. Preserve actual acquisition logs/exits/cache state across compaction.

Use Cargo vendor --locked --versioned-dirs, then independently compare every
vendored package checksum and complete file manifest against its frozen lock and
.cargo-checksum.json. Reject changed/extra/linked payloads. Freeze deterministic
vendor archives, parent/source/lock hashes and per-crate version/license records
in rust-crates.lock.json before guest extraction. Source preparation is separate
from native compilation/tests/owned installation or candidate availability.

Actual source acquisition/verification completed0:418 cargo-c and352 librsvg
registry crates, unchanged parent locks, no host source compilation. Reused public
cache between parents. Archives878eb5b65da8f2fdff3ec2ff54ace08eb717c3b17ff06affd6dda22b88324d52
and67a52cab6d6723c7302369b52fcc3e7db7b2edf043348be7bae4f37f53a53ec7.
Three regressions cover unauthorized registry/path/hash and mutated/extra/linked
cache refusal. Native cargo-c/librsvg and SVG/GTK acceptance remain pending.


The first native cargo-c build stopped at checksum reading before any compilation:
fnv1.0.7 preserves0640 on six public source/legal files after root-owned extraction.
Authenticate the complete vendor file set, change only those files0640→0644 with
unchanged SHA, retain the before/after prepared/operation receipts and original
Cargo101/wrapper1 logs. Future input preparation applies byte-preserving public
vendor readability after integrity checks, before the unprivileged build. Neither
compiler privilege nor source bytes/archive versions change. Resume only the
verified existing source/config/cache in unique job2; native acceptance pending.

Native CargoC correction verified: build0/upstream25PASS/0ignored. The next wrapper
failed only because cargo capi --version emits help0; invoke each plugin directly,
retain help output and run consumer-only recovery3. All11 native checks0, generated
header/pkg-config/shared+static C consumers answer42 and Rust fixture1PASS; four
stage binary hashes unchanged. Owned build-only package installed/post0/0 in110.292s
with9143 legal notices including Rust static runtime. No successful compiler/source
suite replay. Native SVG/GTK/session qualification remains pending.

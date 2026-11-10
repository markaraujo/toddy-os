# ADR-0205 — LocalSearch isolated build and separate native runtime gate

Status: build/stage verified; native runtime and package promotion pending.
Date: 2026-11-10 · Story: B02

Use frozen BLFS13.1-systemd `gnome/localsearch.html`, page SHA256
6183b9afef8f1efeb554e79f93958ac7affe921ab8d748d9ab874abe0f9e0b4e,
and official LocalSearch 3.11.1 source SHA256
7b39a6c28a8acf2b172f15b2fb5ee7c7a3764c447c2f4a14caa239b7ebe61942.
Reuse owned Tinysparql, GExiv2, GLib, GStreamer, image/XML, ICU, UPower and
libseccomp dependencies without foundation upgrades or source patches.

Build core miner, extractor and writeback, retaining seccomp and explicitly
selecting `landlock=enabled`. The upstream source supports this option for
isolated distribution builds on a different build-host kernel; it skips the
configuration-time runtime probe only. Actual installed-kernel Landlock and
LocalSearch behavior remain mandatory separate acceptance. Functional and sandbox
programs are compiled, not silently disabled. Absent optional format dependencies
remain auto-unavailable. Man generation is unselected because a2x is absent;
CLI help and source documentation remain available. This is not an optional
format support or complete documentation acceptance claim.

UID101/read-only-source build1 compiled all276 Ninja steps and staged133 regular
files/186 ELF files. Thirteen original non-slow common/indexer/extract utility
programs passed on builder kernel6.8.0-147-generic. Runtime kernel7.1.8 integration,
three slow programs and functional/extractor/sandbox programs remain unexecuted:
72 registered programs total. The compiler reserve monitor retained at least
17269211136 bytes free, above16GiB, and did not interrupt the compiler.

The original job exited1 after successful compilation/tests/staging because our
collector expected `#define HAVE_LANDLOCK 1` and `HAVE_LIBSECCOMP 1`; upstream
Meson emits exact valueless positive defines. Collection2 alone exited0 after
checking these exact lines, with all compiled/staged file hashes unchanged.
Original source recipe, logs and exit1 remain immutable. The first collector's
pending inventory also compared unqualified registration names with qualified
log names; the public derived report reconciles exact suite+name to distinguish
13 executed from72 pending. Raw first report remains retained. Future recipes
correct both metadata expectations, without changing upstream source or binaries.

[Build proof](../evidence/B02-localsearch-build.json) binds source, original input,
program outcomes, resources, artifact manifests and immutable raw evidence.
No native install, real index/search, sandbox denial, Stop/restart, GNOME or GUI
acceptance is inferred. Before promotion, prepare and run focused native
functional/index/search/denial/cancellation/recovery checks, then the controlled
owned package transaction and installed postconditions. Do not replay extraction,
compilation, accepted programs or staging. Complete all B02, then stop.

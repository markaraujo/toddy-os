# H07 — In-progress final package evidence

Date: 2026-11-05. H07 is NOT complete. Critical final compiler/libc/binutils
suites and the remaining chapter 8 packages are pending.

The first two final packages follow frozen LFS 13.1-systemd sections 8.3/8.4.
Their installs were redirected into DESTDIR staging, inspected for ownership
conflicts and archived as original native .debs before touching the target.
Builder dpkg is infrastructure; no Ubuntu/Debian binary package was imported.
Per-file payload hashes, modes, numeric ownership, recipe hash and frozen
source URLs/hashes are in /var/log/toddy/packages/. Component copyright and
license notices are retained in each installed package. No private data is
included. Native dpkg/APT source builds and signed repository remain pending.

| Step | Recipe/postcheck | Changed paths | Full log SHA-256 |
| --- | --- | ---: | --- |
| man-pages 6.18 | 0 / 0 | 3149 | 83a3821713a820119d6c6a82d0cad0d2e4fe38a2e9752d5a50741f836975435d |
| iana-etc 20260805 | 0 / 0 | 9 | c4232aac759363883ceb0f0bd3c5ae486d65566dd21c7945af7d21799373d51c |
| ownership rejection probe | 0 / 0 | 0 | 7ca5895a8304baa49b4daab6c8e2f8ff68eff4433f210837a5862a3cee33ae4e |

Actual database query reports man-pages 6.18-1 and iana-etc 20260805-1 both
install ok installed. The man page exists, IANA TCP/SSH records match expected
numbers, and /etc/services plus /etc/protocols belong to iana-etc. The latter
are registered conffiles. Archives stay at /var/cache/toddy/packages/.

A staged conflicting package attempted to own /usr/share/man/man2/open.2.
The ownership preflight identified man-pages as owner and rejected it before
building or installing the conflicting archive. Its manifest recorded zero
installed-path changes; the original file hash and owner remained unchanged.
No --force-overwrite was used.

Full local evidence: .local/logs/h07/. Recovery checkpoint before final base:
h06-ready. Security overlay and actual critical suite results must be recorded
before the final libc can be accepted. No G1 or release claim is made.

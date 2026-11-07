# ADR-0100: Classify File's exact source-regenerated recognition database

- Date: 2026-11-07
- Status: Native source regeneration and two negative controls passed

Full H11 assembly passed ownership, attribution, runtime and fresh identity,
then its unsuppressed key-marker scan found seven files. Six are the already
qualified OpenSSL manual placeholders. The seventh is the native File 5.48
format-recognition database, /usr/share/misc/magic.mgc. The earlier small marker
fixture did not include the File package.

The frozen magic/Magdir/ssh source explicitly recognizes OpenSSH, unencrypted
and encrypted private-key armor headers as file-format signatures. Retain those
useful recognition rules. Accept only this exact database generation, after
verifying its image package/record/archive, frozen source archive and native
compiler payload. Follow the frozen magic/Makefile.am recipe: collect all 358
named magic fragments and run the accepted native file -C -m magic. Require the
complete generated binary to match the image SHA-256 byte for byte. Keep every
raw scan finding; record this classification separately from manual examples.

Actual native compilation exited zero, with no diagnostics, producing:
`c2f4e7e55b0ee33c181ada80b065f9f8a58633c9806e8bd3353253c68324f268`.
Changed database bytes and identical bytes at an unrelated path both remain
unresolved scan findings. The original image is unchanged. No arbitrary binary,
package, directory or upstream test key is exempted. Full credential/identity
review and final image/boot acceptance remain separate obligations.

Sources and alternatives: frozen file-5.48.tar.gz SHA-256
ed14656883b23a364b4057c05595d93252da9bc473d30106519519d0da141283;
magic/Makefile.am SHA-256
4871c42e2fa589837f80b333aff9376dca6ef6558a6ae70b50833d744d769dde;
magic/Magdir/ssh SHA-256
38e6e7049f18a557950a50167c40a4dff7529bbfdaaa240d612889431cd382fd.
Deleting the database would break file recognition. Suppressing all binary
markers or trusting only a pathname would hide real unexpected inputs. Exact
source regeneration supplies evidence without changing upstream functionality,
source versions or the requirement to exclude development credentials.

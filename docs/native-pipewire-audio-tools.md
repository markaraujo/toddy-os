# Standalone native PipeWire audio tools

`pipewire-audio-tools` 1.6.8-1+toddy1 owns the already compiled native pw-cat
binary and its nine upstream aliases. It leaves `pipewire` itself at the exact
accepted 1.6.8-1+toddy1 revision, including all649 library/config/notice entries
and the five GNOME/audio reverse dependency pins. It neither adds a versioned
Provides substitute nor retargets transitive dependencies.

First require the actual [controlled base restoration](native-pipewire-base-recovery.md)
full-root success0/0, exact own receipt and APT0. Preserve failed upgrade1 and its
revision2 archive/record. The standalone producer refuses missing restoration,
changed old bytes/pins or any preexisting tool/package/stage outcome.

From `/opt/toddy-build`, the sole guest writer runs:

```sh
python3 scripts/build/run_step.py b09-pipewire-audio-tools-2 \
  scripts/build/phase2/pipewire_audio_tools_install.sh \
  scripts/build/phase2/pipewire_audio_tools_check.sh --user root
```

No build is dispatched. The producer calls the **unchanged frozen**
`pipewire_tools_native.qualify()` against successful `pipewire-tools-build-2`,
its exact source/prepared/job/exit/SDK/custody pins and original private tool
stage. Restored PipeWire1 bytes are identical to the library used during that
compile, so no rebuild is necessary. Native ELF provider/RPATH checks repeat.
All frozen voice/compiler inputs and shared source/license/audit files remain
unchanged.

The new payload contains only `/usr/bin/pw-cat`, its exact relative aliases and
`/usr/share/doc/pipewire-audio-tools`. Exact old source notices/copyright are read
from the authenticated retained old archive and copied into that separate doc
namespace, preserving their bytes and origin. The selected six upstream C files
and five local headers are retained verbatim as legal/source documentation from
the verified protected frozen source archive; their actual per-file MIT headers
are checked. No mutable installed-root legal file is copied, and the original
PipeWire copyright/doc namespace is unchanged. A source manifest binds these
copies, source archive SHA, actual compile2/stage hashes, recovery ledger and new
producer/recipe inputs.

Depends is the actual exact old PipeWire1, libsndfile1.2.2, glibc2.44 and GCC
runtime16.2.0 native revisions. Standard native stage_package/run_step owns the
first package transaction, full-root before/after manifest and postcheck. The
16 GiB reserve and measured copy/staging allowance remain mandatory. There are
no conffiles, libraries, service units, automatic activation, models, credentials
or permission grants in this tools payload.

Postcheck verifies native old/new package identities, every unchanged649 base
row, the same five dependency records, original successful compile2/tool hashes,
all newly installed bytes/modes/links and package-owned namespace, actual help/
compiled-linked1.6.8 output, empty Dpkg audit and APT0. The own receipt is
`/var/log/toddy/phase2/pipewire-audio-tools-install-1.json`, final
`state: native-audio-tools-package-verified`, `old_library_payload_unchanged: true`,
integer `apt_check_exit: 0`, restoration receipt SHA, new record/archive SHA and
actual `native_pwcat_sha256`. Its manifest retains restoration full-root success/
manifest/receipt hashes, rejected upgrade hashes, old base pins, prepared/job/
exit/tool-stage/source/legal hashes and direct ELF closure. Full-root success0/0
remains separately required.

`actual_audio_process_qualification` deliberately remains `pending`. A real new
voice process namespace must consume this restoration + separate tools package
ledger and test actual capture/playback/control; no failed process is replayed,
no success is copied from fixtures and no runtime catalog is fabricated. The
source unit tests execute only synthetic archive/stage checks, never native
Dpkg, audio or a VM.


Attempt1 stopped before native package writes (changed paths0): the child
packager inherited private umask077 and created a DEBIAN directory0700. Its
stage/receipt/failed ledger remain. Attempt2 uses fresh stage/receipt/step2 and
sets umask022 only in the native packager child; the coordinator evidence stays
private. The actual attempt2 recipe and independent postcheck passed0/0 without
recompiling the frozen tool. Base PipeWire1 and APT consistency remained intact.

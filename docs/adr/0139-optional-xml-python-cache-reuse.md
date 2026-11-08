# ADR-0139: Reuse the accepted XML cache for its optional Python target

- Date: 2026-11-08
- Status: Native binding and independent owned installation qualified
- Sources: frozen libxml2-2.15.3 meson.build, doc/meson.build,
  python/meson.build and48 original python/tests scripts; ADR-0110

AppStream's actual data recipe uses itstool, which imports the native libxml2
Python binding. The accepted2.15.3 core was built with Python disabled. Its
optional Python flag adds documentation metadata and the binding subdirectory;
it does not add a core C configuration feature. Preserve that version and the
accepted3904 C cases rather than rebuild/retest the foundation.

Use the original private compiler work/cache with unchanged /src and
/build/compile paths, one writer, read-only installed dependencies/source and
UID101/caps0/NoNewPrivs isolation. Snapshot existing core ELF hashes, enable only
the Python option, and build the actual introspected shared-module target. Its
name includes the CPython ABI suffix. Run the48 unmodified scripts with their
relative fixtures in a private writable source copy. Install with no rebuild
into private scratch, then select only the two Python modules and extension
into a separate optional-binding stage. Do not mutate the original core stage.

The original nested-cache alias was hidden by the sandbox's nonrecursive work
bind. That job failed before mutation, and the verified unused alias was
unmounted. The subsequent configure completed; a bare target-name lookup then
failed before compilation. Preserve both failures. Recovery verifies enabled
options and all99 original ELF hashes before resuming after configuration;
never reconfigure an uncertain cache. Actual binding compilation, all48 scripts,
staging and99 unchanged ELF hashes subsequently passed.

The staged semantic consumer proves Unicode XPath/document lifetime and the
NO_XXE external-entity refusal with a successful external-file positive control.
Its fixture contains public generated text, never a credential. Independent
Python-only native ownership and the installed semantic consumer passed0/0.
The first promotion rejected a generated .pyc before copying/installing payload.
A private probe-only recovery removed that exact derived cache and disabled
bytecode generation; the three intended files and original99 ELFs were retained.
Keep the original failed/preflight records and successful native-2 transaction.
No graphical session, application or physical hardware acceptance follows from
this package. Keep the source archive, license notices, original C evidence,
optional-target logs and independent installation/verification receipts.

# ADR-0116: Native installer feasibility and typed JSON plan boundary

- Date: 2026-11-07 America/Sao_Paulo
- Status: Accepted B01 integration choice; B12 installation acceptance pending
- Scope: Existing Calamares/Qt route, no architecture replacement

Calamares3.4.3 actually compiles/stages against native Qt6.11.2, accepted
Python3.14.10 and its unchanged bundled Pybind11 2.11.1. The real Python Job API
executes the synthetic no-write target-plan fixture, returns a successful
JobResult, and the native executable reports its version. See
[measured scope and stage identity](../evidence/B01-calamares-native-probe.json)
and [native prerequisite consumers](../evidence/B01-installer-prerequisites.json).
No core Python/OpenSSL upgrade, alternate installer or hosted runtime is needed.

Build only QtBase/Svg/LinguistTools, ECM6.29, CoreAddons6.29 and yaml-cpp0.9 for
this boundary. CoreAddons has no QML/PySide dependency in the selected build.
QtBase uses offscreen raster platforms; native GNOME/Wayland/font/visual work is
still required. All upstream install modules, QML and Polkit policy installation
are disabled **for this no-write fixture**. This does not remove final installer
authorization, partition/boot/package-trust or recovery requirements. Reconfigure
the final supported display/module closure in B02/B12; do not publish this SDK
stage as an installable release.

Calamares exports the Python Job constructor, while its concrete virtual methods
are hidden. Consumers use the public `Calamares::Job` virtual interface, matching
upstream PythonJobModule. The original incorrect concrete consumer link failure
is retained; no upstream visibility or ABI patch was necessary.

The successful raw-map fixture exposed Python booleans arriving as QVariant
integers. Use a bounded schema-versioned JSON **string** across the Calamares
GlobalStorage boundary for Toddy plan/handoff bodies. The native consumer checks
actual QJson Boolean types before conversion, not truthiness of numbers. The
affected corrected fixture passed with literal true/false, version1, deferred
extras and nine expected invalid-input rejections. Production B12 must apply its
strict parser, schema/semantic validation and ownership/atomic handoff checks;
this small fixture does not implement them or grant installation authority.

Preserve original job1 shell-tail failure, job2 concrete-symbol link failure and
job3 successful raw-map output. Job4 verifies the selected JSON boundary without
recompiling/reinstalling upstream dependencies. The compiler sandbox remains
unprivileged with read-only native/source inputs and no disk devices/external
network. Native package transactions retain full-root verification (ADR-0110).

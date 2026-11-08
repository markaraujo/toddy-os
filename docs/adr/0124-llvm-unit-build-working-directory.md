# ADR-0124: LLVM unit tests use the normal build working directory

- Date: 2026-11-08
- Status: Accepted affected-test correction; native corrected result pending

LLVM22.1.8 compiler4451 and critical dependency1068 compilation steps completed.
The first lit launch lacked psutil and ran no cases. Native psutil7.2.2 process
timeout/tree/terminate/kill/reap checks and owned installation then passed.
Resume3 reused all dependency outputs with an actual no-op Ninja dry-run.

Actual LLVM unit report contains10501 PASS and one FAIL:
VFSFromYAMLTest.RelativePaths. Its original source
llvm/unittests/Support/VirtualFileSystemTest.cpp takes the process working
directory and removes CWD.size()+1 from an absolute path. At the harness's root
working directory this strips the first character, yielding elative/path.h.
The frozen BLFS13.1 LLVM instructions execute tests from the build directory.
This is a test working-directory mismatch, not an accepted compiler failure.

Run the affected SupportTests group (1646 recorded cases) from /build/compile
without recompiling or changing source/expectations. Reuse the8856 other passing
unit cases. Preserve the original failed report, exact binary hashes and actual
corrected native report. A deterministic merge requires identical affected names,
all corrected cases PASS and exactly the known original failure. Unknown/additional
failures, missing cases and skips cannot qualify. Label the combined record as
derived qualification; never replace the raw failed report or invent its exit0.

Require the six remaining ADR0121 suites, poison-select regression, unchanged
compiler/test binaries, reserve and staging gates. Native package/JIT/libclang/
ownership and final image tests remain pending. Fresh qualification starts in the
normal build directory and checks psutil before compiling test dependencies.
This does not rerun the completed compiler or weaken any runtime security boundary.

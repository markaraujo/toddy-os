# ADR-0121: Native LLVM scope and compiler validation

- Date: 2026-11-08
- Status: Accepted technical selection; execution evidence remains required

## Context

B02 needs the frozen LLVM22.1.8 for Mesa/native Rust dependencies and Clang/libclang
for source-build consumers. The accepted foundation compiler/libc are unchanged.
Frozen BLFS13.1-systemd general/llvm.html (page SHA256
fbadf2aea39a17abf64a3241f1e4958249d2a9ad519b7e472cb4c56478a565c2)
estimates4.7GB build/1.1GB installed and23GB additional for check-all. Actual target
has38GiB available with16GiB reserve. A complete additional matrix does not fit that
reserve. The owner requires change-based basic checks and explicit source-backed
selection for critical compiler tests, not an untested compiler or a repeated
foundation build.

LLVM's original source archive SHA256
922f1817a0df7b1489272d18134ee0087a8b068828f87ac63b9861b1a9965888
contains the ORC SharedMemoryMapper and ExecutorSharedMemoryMapperService using
shm_open/mmap. The compiler namespace has private IPC but initially no POSIX shared
memory filesystem. Tests need that dependency without exposing guest/host shm.

## Decision

Build the frozen LLVM core and Clang/libclang, host X86 plus AMDGPU code-generation
backends, shared LLVM, RTTI/FFI and installed FileCheck. Apply the exact required
book patch before immutable input hashing: SelectionDAG select/load poison fix
from Rust LLVM commit abcef279cd33492fe8301c8873fc535fa4dbf0d5, archive patch SHA256
4a2084f9714f2f3babc0ed58065c3a6b83cd2828ea19aec1518995a6d2376187.
No version substitution, native-CPU-only flags or foundation compiler replacement.
Compiler-rt/sanitizer runtimes and other optional LLVM projects are not selected
for this desktop prerequisite; do not advertise those tools as qualified.

Add a256MiB private tmpfs at /dev/shm only inside the existing compiler mount/IPC
namespace. Preserve UID101, zero capabilities, NoNewPrivs, read-only inputs and
installed dependencies, no egress, private descriptors and exclusive parent lock.
Qualify actual POSIX shared memory, child read/execute mapping with write then
read/execute protection, parent visibility denial and existing confinement checks
before dispatching a compiler with this namespace version. This does not change
global security, mount the host shm or authorize a second guest writer.

Compile with four jobs and one link job on the measured12-vCPU/12GiB builder.
Before tests require at least24GiB available (16GiB reserve plus8GiB test headroom);
checkpoint instead of silently consuming the reserve. Healthy builds are monitored,
not restarted because compilation exceeds a diagnosis window.

Required native validation for this selection:

- LLVM and Clang unit suites, including IR/support and ORC/JIT APIs.
- LLVM lit Transforms, X86 CodeGen and ExecutionEngine suites, including the exact
  patched select-of-load-poison regression and selected X86 reference updates.
- Clang C/C++ CodeGen lit suites. Preserve unsupported/expected-failure counts;
  they are not passes. Any unexpected failure blocks package acceptance pending
  bounded diagnosis or a separately recorded, source-backed resolution.
- Installed actual C/C++ compilation/link/execution, libclang load, LLVM ORC JIT,
  FileCheck, default PIE/stack-protection checks, ownership/ABI and native audit.

Save actual exit statuses, exact inputs, raw result/log hashes and counts. No result
is preaccepted by this ADR. Full cross-target/compiler-rt/check-all/benchmark coverage
is not claimed; later changed consumers invalidate only their affected proof.
Rust still needs its own critical validation and authenticated bootstrap inputs.

## Consequences

This retains essential compiler/JIT coverage with measured disk/memory bounds and
makes optional omitted coverage explicit. The first installed package remains
unqualified until its actual selected checks and native postconditions pass. Final
Mesa/Rust/Firefox and GNOME runtime checks remain required for B02/B13/G2; compiler
success alone does not establish graphics, hardware or UI acceptance.

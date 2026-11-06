# ADR-0016: Bash descriptor isolation and exact reference classification

- Status: Accepted; full corrected-suite retry must pass classification
- Date: 2026-11-06
- Scope: H07 Bash 5.3, frozen LFS 13.1-systemd section 8.39

## Evidence and diagnosis

The complete initial PTY suite visited all 86 run-* groups. Its wrapper returned
zero, as upstream run-all always does, but independent comparison rejected ten
diff lines. No installation occurred. Do not treat that raw zero as acceptance.

Focused execution showed descriptor 4 was an inherited pipe. With the same
built Bash, tester, PTY and tests, closing descriptors 3/4 before make removed
the exec17.sub invalid-descriptor and BASH_XTRACEFD differences. Running make
serially alone did not close the inherited pipe. A first focused probe also
omitted run-all's TMPDIR initialization; its unrelated permission diagnostics
are retained. The corrected probe sets TMPDIR=/tmp. Full suites use unmodified
run-all, which initializes TMPDIR itself.

The remaining execscript differences reorder otherwise identical trap listings
because Linux signal numbers differ from the expected fixture's ordering.
The run-execscript source explicitly warns about different UNIX signal numbers.
The remaining printf7.sub difference concerns an out-of-range inline precision
9223372036854775825: this target reports EOVERFLOW rather than emitting XY.
It is not a normal finite-precision formatting difference. Both exact remaining
sequences occur in the official LFS 13.1 Bash 5.3 test log on another machine.
The official log contains additional locale/resource/descriptor differences
which are deliberately not accepted as exceptions here.

## Decision and alternatives

Close the inherited descriptors in a new child before invoking make -j1 tests
inside Expect's tester-owned PTY, then repeat all 86 groups. Keep the original
raw run and focused logs. Do not modify tests, expected fixtures or upstream
Bash code. Stage/install only after complete group coverage and classification.

Allow only the two exact group-specific diff sequences recorded in
config/bash-test-reference.json, and verify their presence in the hash-pinned
primary reference before use. Unknown, partial, misplaced or additional
mismatches, missing/duplicate groups and fatal diagnostics remain rejected.
Independent tests cover those negative cases. Native shell execution and
ordinary printf/trap behavior remain separately tested after installation.

Ignoring every diff based on make's zero exit would hide failures. Editing the
fixture would erase evidence. Accepting every difference in the official log
would conceal missing locales or descriptor leaks we can fix. Backporting an
unverified printf change would change frozen source behavior without necessity.
The selected qualification retains the source-known extreme-precision outcome
explicitly; no all-pass Bash-suite claim is made. Revisit if application code
requires the nonportable overflowing precision behavior.

## Sources

- [LFS 13.1-systemd 8.39](https://www.linuxfromscratch.org/lfs/view/13.1-systemd/chapter08/bash.html), frozen book hash in config/books.lock.json.
- Bash 5.3 tests/run-execscript, exec.right, exec17.sub, printf7.sub,
  set-x1.sub and run-all in the SHA-pinned source archive; code read directly.
- [Official LFS 13.1 Bash 5.3 test log](https://www.linuxfromscratch.org/lfs/build-logs/13.1/i7-14700K/test-logs/837-bash-5.3),
  SHA-256 ff45b725dc0d45449a595aaffb9bbc90e70ca4ecc7320289404ee9a64c190e58.

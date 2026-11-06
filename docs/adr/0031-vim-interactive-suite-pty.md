# ADR-0031: Run unchanged interactive Vim tests under a tester-owned PTY

- Status: Focused correction verified; fresh complete retry pending
- Date: 2026-11-06
- Scope: Frozen Vim 9.2.1201 upstream suite, including all GLVS tests

The first complete suite had many premature Vim exits in input-related tests.
Its make process inherited /dev/null stdin. No package was staged or installed.
Preserve the full check log, per-test reports and verified-download events.

Focused upstream Test_getchar and Test_ex_mode_with_global both actually execute
and pass under a tester-owned PTY, with result files and messages checked. An
initial anchored filter omitted the function parentheses and matched nothing;
that zero-test run is not evidence of success. Corrected probes execute one test
each. A root Expect launcher followed by su was unsuitable; run Expect itself
as tester, following the already validated Bash suite pattern in ADR-0016.

Fresh-extract the verified source archive, preserve the previous complete tree,
and repeat all tests without TEST_FILTER/TEST_SKIP_PAT/TEST_MAY_FAIL. Native
Expect holds a real controlling PTY, sets 24x80 terminal dimensions and closes
inherited descriptors 3/4 in the child before running make -j1 test. Use UTF-8,
the installed terminal description and the unchanged verified-download PATH
wrapper. Capture EOF/wait status, reject signal/system errors, and preserve all
raw output. No source/test/assertion is removed or changed to accept failure.
Only complete-suite success, all four actual guarded plugin versions and native
editor postchecks permit installation/acceptance.

Sources: actual frozen src/testdir/{README.txt,Makefile,runtest.vim},
 test_vim9_builtin.vim/test_ex_mode.vim, archived initial reports and actual
focused messages/result files; existing source-validated Bash PTY execution.


The first full PTY attempt exposed a launcher environment defect: su's selected
Expect interpreter became SHELL=/usr/bin/expect. The PO checker invokes
system("msgfmt ...") and therefore failed before script tests. A focused whole
PO-check run under the same PTY passes when SHELL=/bin/bash is explicit. Preserve
that failed log; reuse the verified compiled binary/code/tests, reset only test
outputs and repeat complete make test with the corrected shell. Verify all
planned NEW_TESTS_RES exist as well as the actual zero-failure summary. The
success label is case-sensitive Failed: 0, as defined by util/summarize.vim.

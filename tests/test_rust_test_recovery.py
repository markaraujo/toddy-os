import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts/build/phase2'))
from rust_std_tests import qualify_preserved_log


def terminal_log():
    sections = []
    for binary in ['alloctests-abc', 'coretests-def', 'std-ghi']:
        sections.append('     Running tests/lib.rs (/build/deps/' + binary + ')\n'
                        'test result: ok. 501 passed; 0 failed; 0 ignored; '
                        '0 measured; 0 filtered out; finished in 1s\n')
    sections.append('     Running tests/pipe_subprocess.rs (/build/deps/pipe)\n'
                    'Test pipe_subprocess.rs success\n')
    return '\n'.join(sections) + 'Build completed successfully in 0:01:42\n'


class RustTestRecovery(unittest.TestCase):
    def test_complete_native_result(self):
        self.assertEqual(sum(r['passed'] for r in qualify_preserved_log(terminal_log())), 1503)

    def test_missing_or_failed_terminal_rejected(self):
        for text in [terminal_log().replace('successfully', 'unsuccessfully'),
                     terminal_log().rsplit('Build completed', 1)[0]]:
            with self.assertRaises(AssertionError):
                qualify_preserved_log(text)

    def test_unknown_missing_driver_result_rejected(self):
        text = terminal_log().replace('Test pipe_subprocess.rs success', '')
        with self.assertRaises(AssertionError):
            qualify_preserved_log(text)

    def test_failed_or_filtered_cases_rejected(self):
        for field, value in [('0 failed', '1 failed'), ('0 filtered out', '1 filtered out')]:
            with self.assertRaises(AssertionError):
                qualify_preserved_log(terminal_log().replace(field, value, 1))


if __name__ == '__main__':
    unittest.main()

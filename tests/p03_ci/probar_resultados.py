#!/usr/bin/env python3
"""Pruebas del clasificador CI; ninguna acredita la recuperacion real de Core."""
from pathlib import Path
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts/p03'))
from ejecutar_bateria import aggregate, classify_case, classify_suite


class Results(unittest.TestCase):
    def test_clean(self):
        self.assertEqual(classify_case('OK', False), 'PASS')

    def test_asan_even_zero(self):
        self.assertEqual(classify_case('ERROR: AddressSanitizer: heap-use-after-free', False), 'FAIL_SANITIZER')

    def test_ubsan_even_zero(self):
        self.assertEqual(classify_case('runtime error: signed integer overflow', False), 'FAIL_SANITIZER')

    def test_lsan_even_zero(self):
        self.assertEqual(classify_case('LeakSanitizer: detected memory leaks', False), 'FAIL_SANITIZER')

    def test_ptrace_is_not_pass(self):
        self.assertEqual(classify_case('LeakSanitizer does not work under ptrace', True), 'BLOCKED_INFRASTRUCTURE')

    def test_real_failure_beats_ptrace(self):
        self.assertEqual(classify_case('LeakSanitizer does not work under ptrace\n{"ok": false}', True), 'FAIL_PROGRAM')

    def test_sanitizer_beats_ptrace(self):
        self.assertEqual(classify_case('LeakSanitizer does not work under ptrace\nAddressSanitizer:DEADLYSIGNAL', True), 'FAIL_SANITIZER')

    def test_summary_failure_even_zero(self):
        self.assertEqual(classify_case('{"status": "FAIL"}', False), 'FAIL_PROGRAM')

    def test_unknown_sanitizer_report(self):
        self.assertEqual(classify_case('LeakSanitizer: unexpected diagnostic', False), 'FAIL_SANITIZER')

    def test_skipped_is_not_pass(self):
        self.assertEqual(classify_case('', False, True), 'FAIL_NOT_RUN')

    def suite(self, content, rc=0, count=1):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'junit.xml'
            path.write_text(content)
            return classify_suite(path, rc, count)['status']

    def test_missing_tests(self):
        self.assertEqual(self.suite('<testsuite/>'), 'FAIL_TEST_COUNT')

    def test_duplicate_tests(self):
        self.assertEqual(self.suite('<testsuite><testcase name="x"/><testcase name="x"/></testsuite>', count=2), 'FAIL_TEST_COUNT')

    def test_malformed_junit(self):
        self.assertEqual(self.suite('not xml'), 'FAIL_MISSING_JUNIT')

    def test_missing_junit(self):
        with tempfile.TemporaryDirectory() as temp:
            self.assertEqual(classify_suite(Path(temp) / 'missing.xml', 0, 1)['status'], 'FAIL_MISSING_JUNIT')

    def test_unnamed_case(self):
        self.assertEqual(self.suite('<testsuite><testcase/></testsuite>'), 'FAIL_TEST_COUNT')

    def test_ctest_failure_even_green_xml(self):
        self.assertEqual(self.suite('<testsuite><testcase name="x"/></testsuite>', rc=8), 'FAIL_CTEST')

    def test_contaminated_junit(self):
        self.assertEqual(self.suite('<testsuite><testcase name="x"><system-out>AddressSanitizer:DEADLYSIGNAL</system-out></testcase></testsuite>'), 'FAIL')

    def test_truncated_junit_is_not_pass(self):
        xml = '<testsuite><testcase name="x"><system-out>[This part of the test output was removed since it exceeds the threshold of 1024 bytes.]</system-out></testcase></testsuite>'
        self.assertEqual(self.suite(xml), 'FAIL')

    def test_aggregate_blocked(self):
        self.assertEqual(aggregate(['PASS', 'BLOCKED_INFRASTRUCTURE']), ('BLOCKED_INFRASTRUCTURE', 2))

    def test_aggregate_known_failure(self):
        self.assertEqual(aggregate(['FAIL_PROGRAM', 'BLOCKED_INFRASTRUCTURE']), ('FAIL', 1))

    def test_aggregate_unknown_or_empty(self):
        for values in [[], ['NOT_RUN'], ['SKIPPED']]:
            with self.subTest(values=values):
                self.assertEqual(aggregate(values), ('FAIL', 1))


if __name__ == '__main__':
    unittest.main(verbosity=2)

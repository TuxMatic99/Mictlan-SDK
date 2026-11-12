"""Regresiones contra falsos verdes y perdida de fallos ante ptrace."""
import json
import subprocess
from pathlib import Path
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts/p03'))
from ejecutar_bateria import aggregate, classify_case
from regresiones_core import validate_inventory, run_core, run_modular


class CoreResults(unittest.TestCase):
    def test_program_and_ptrace(self):
        self.assertEqual(classify_case('No se pudo abrir el archivo: ejemplos/coverage.lat\n'
            'LeakSanitizer does not work under ptrace', True), 'FAIL_PROGRAM')

    def test_assertion_even_zero(self):
        for text in ['P033_ASSERT linea 1', 'FAIL linea 2', 'Assertion x failed']:
            self.assertEqual(classify_case(text, False), 'FAIL_PROGRAM')

    def test_inventory_count(self):
        for tests in [[], [{'name': 'x'}, {'name': 'x'}]]:
            with self.assertRaises(ValueError): validate_inventory(tests, 1)

    def test_cannot_invert_or_skip(self):
        for prop in ['WILL_FAIL', 'DISABLED', 'SKIP_RETURN_CODE', 'SKIP_REGULAR_EXPRESSION', 'ENVIRONMENT_MODIFICATION']:
            with self.assertRaises(ValueError):
                validate_inventory([{'name': 'x', 'properties': [{'name': prop, 'value': 1}]}], 1)

    def test_unreviewed_environment(self):
        with self.assertRaises(ValueError):
            validate_inventory([{'name': 'x', 'properties': [{'name': 'ENVIRONMENT', 'value': ['LD_PRELOAD=bad.so']}]}], 1)

    def test_original_leak_override_is_not_executed(self):
        with tempfile.TemporaryDirectory() as tmp:
            calls = []
            test = {'name': 'known', 'command': ['/test/bin'], 'properties': [
                {'name': 'WORKING_DIRECTORY', 'value': '/original'},
                {'name': 'ENVIRONMENT', 'value': ['ASAN_OPTIONS=detect_leaks=0']}]}
            def run(name, command, **kwargs):
                calls.append((name, command, kwargs))
                return (0, json.dumps({'tests': [test]}), '') if name == 'core-inventory' else (
                    86, '', 'ERROR: AddressSanitizer: heap-use-after-free')
            result = run_core(run, 'ctest', Path('/source'), Path('/build'), Path(tmp), 1,
                              classify_case, aggregate, {'known'})
            self.assertEqual(result['status'], 'FAIL')
            self.assertTrue(result['cases'][0]['known_failure'])
            self.assertEqual(calls[1][1], ['/test/bin'])
            self.assertEqual(calls[1][2], {'timeout': 60, 'cwd': '/original'})
            self.assertIn('failure', (Path(tmp) / 'core.xml').read_text())

    def test_blocked_is_not_junit_skip(self):
        with tempfile.TemporaryDirectory() as tmp:
            def run(name, command, **kwargs):
                return (0, '{"tests":[{"name":"x","command":["x"]}]}', '') if name == 'core-inventory' else (
                    86, '', 'LeakSanitizer does not work under ptrace')
            result = run_core(run, 'ctest', Path('/s'), Path('/b'), Path(tmp), 1,
                              classify_case, aggregate, set())
            self.assertEqual(result['status'], 'BLOCKED_INFRASTRUCTURE')
            xml = (Path(tmp) / 'core.xml').read_text()
            self.assertIn('<error', xml)
            self.assertNotIn('<skipped', xml)

    def test_missing_coverage_beats_buffered_output_and_ptrace(self):
        with tempfile.TemporaryDirectory() as tmp:
            def run(name, command, **kwargs):
                return (0, '{"tests":[{"name":"coverage","command":["binary","missing.lat"]}]}', '') if name == 'core-inventory' else (
                    86, '', 'LeakSanitizer does not work under ptrace')
            result = run_core(run, 'ctest', Path(tmp), Path(tmp), Path(tmp), 1,
                              classify_case, aggregate, {'coverage'})
            self.assertEqual(result['status'], 'FAIL')
            self.assertEqual(result['cases'][0]['status'], 'FAIL_CONFIGURATION')

    def test_extension_uses_selected_binary_not_source_neighbor(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            core, build, output = root / 'core', root / 'selected', root / 'output'
            (core / 'tests').mkdir(parents=True)
            (core / 'ejemplos').mkdir()
            build.mkdir(); output.mkdir()
            (root / 'build-core-debug').mkdir()
            for directory, value in [(build, 'selected'), (root / 'build-core-debug', 'wrong')]:
                binary = directory / 'mictlan'
                binary.write_text('#!/bin/sh\necho ' + value + '\n'); binary.chmod(0o755)
            (core / 'tests/run_extension_regression.sh').write_text(
                '#!/bin/bash\nraiz="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"\n'
                'test "$("$raiz/../build-core-debug/mictlan")" = selected\n')
            def run(name, command, **kwargs):
                if name != 'modular-extension': return 0, '', ''
                p = subprocess.run(command, capture_output=True, text=True)
                return p.returncode, p.stdout, p.stderr
            result = run_modular(run, core, build, output, classify_case, aggregate)
            self.assertEqual(result['status'], 'PASS')
            self.assertFalse((output / 'extension-layout').exists())


if __name__ == '__main__': unittest.main(verbosity=2)

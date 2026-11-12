#!/usr/bin/env python3
"""Prueba la clasificacion del control LSan con trazas sinteticas conocidas."""
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
path = Path(__file__).resolve().parents[2] / 'scripts/p03/verificar_errores.py'
spec = importlib.util.spec_from_file_location('p03_runner', path)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


def result(code, message=''):
    return {'returncode': code, 'streams': ['', message]}


def main():
    clean = result(0)
    leak_message = 'ERROR: LeakSanitizer: detected memory leaks\nSUMMARY: AddressSanitizer: 137 byte(s) leaked in 1 allocation(s).'
    leak = result(86, leak_message)
    blocked = result(86, 'LeakSanitizer has encountered a fatal error.\nHINT: LeakSanitizer does not work under ptrace (strace, gdb, etc)')
    scenarios = {
        'valido': (clean, leak, 'PASS'),
        'limpio_bloqueado': (blocked, leak, 'BLOCKED_INFRASTRUCTURE'),
        'fuga_bloqueada': (clean, blocked, 'BLOCKED_INFRASTRUCTURE'),
        'detector_silencioso': (clean, clean, 'FAIL_PREFLIGHT'),
        'limpio_con_fuga': (leak, leak, 'FAIL_PREFLIGHT'),
        'uaf_y_bloqueo': (result(86, 'ERROR: AddressSanitizer: heap-use-after-free'), blocked, 'FAIL_PREFLIGHT'),
        'fuga_sin_error': (clean, result(0, leak_message), 'FAIL_PREFLIGHT'),
        'timeout': (result('TIMEOUT'), leak, 'FAIL_PREFLIGHT'),
        'cantidad_distinta': (clean, result(86, leak_message.replace('137', '1')), 'FAIL_PREFLIGHT'),
    }
    name = sys.argv[1]
    clean_case, leak_case, expected = scenarios[name]
    actual = runner.classify_lsan(clean_case, leak_case)
    print(json.dumps({'scenario': name, 'expected': expected, 'actual': actual}))
    return 0 if actual == expected else 1


if __name__ == '__main__':
    raise SystemExit(main())

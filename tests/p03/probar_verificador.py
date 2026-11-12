#!/usr/bin/env python3
"""Regresiones del oraculo; los informes de sanitizadores son simulados."""
import argparse
import json
import os
from pathlib import Path
import shlex
import subprocess
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cmake', required=True)
    parser.add_argument('--caso', choices=['tipo', 'rango'], required=True)
    parser.add_argument('--escenario', required=True)
    args = parser.parse_args()
    encabezado, diagnostico = {
        'tipo': ('=== PRUEBA DE ERROR DE TIPO ===', 'El parametro debe de ser un decimal'),
        'rango': ('=== PRUEBA DE DESBORDAMIENTO ===', 'ciencia.sumar2: resultado fuera de rango'),
    }[args.caso]
    avisos = {
        'asan': 'ERROR: AddressSanitizer: heap-use-after-free',
        'ubsan': 'SUMMARY: UndefinedBehaviorSanitizer: undefined-behavior',
        'lsan': 'ERROR: LeakSanitizer: detected memory leaks',
        'ubsan_sin_nombre': 'example.c:1:2: runtime error: signed integer overflow',
        'asan_deadlysignal': 'AddressSanitizer:DEADLYSIGNAL',
        'lsan_ptrace': 'LeakSanitizer does not work under ptrace (strace, gdb, etc)',
        'lsan_fatal': 'LeakSanitizer has encountered a fatal error.',
        'uaf_y_ptrace': 'ERROR: AddressSanitizer: heap-use-after-free\nLeakSanitizer has encountered a fatal error.',
    }
    opciones_invalidas = {
        'lsan_exitcode_cero': ('LSAN_OPTIONS', 'exitcode=0'),
        'lsan_exitcode_ceros': ('LSAN_OPTIONS', 'exitcode=00'),
        'asan_sin_fugas': ('ASAN_OPTIONS', 'detect_leaks=0'),
        'lsan_sin_cierre': ('LSAN_OPTIONS', 'leak_check_at_exit=0'),
        'ubsan_sin_parada': ('UBSAN_OPTIONS', 'halt_on_error=0'),
        'log_externo': ('ASAN_OPTIONS', 'log_path=/tmp/p03-oculto'),
        'log_duplicado': ('ASAN_OPTIONS', 'log_path=stderr:log_path=/tmp/p03-oculto'),
        'supresion': ('LSAN_OPTIONS', 'suppressions=/tmp/p03-supresiones'),
    }
    esperado = 'PASS'
    stdout = encabezado + '\n'
    stderr = diagnostico + '\n'
    final = 'exit 1\n'
    escenario = args.escenario
    clave = escenario[:-7] if escenario.endswith('_stdout') else escenario
    if clave in avisos:
        esperado = 'BLOCKED_INFRASTRUCTURE' if clave in ['lsan_ptrace', 'lsan_fatal'] else 'FAIL_SANITIZER'
        if escenario.endswith('_stdout'):
            stdout += avisos[clave] + '\n'
        else:
            stderr += avisos[clave] + '\n'
    elif escenario == 'salida_cero':
        final, esperado = 'exit 0\n', 'FAIL_EXIT'
    elif escenario == 'sin_diagnostico':
        stderr, esperado = 'Otro error\n', 'FAIL_DIAGNOSTIC'
    elif escenario == 'salida_extra':
        stdout += 'NO_DEBERIA_CONTINUAR\n'
        esperado = 'FAIL_OUTPUT'
    elif escenario == 'timeout':
        final, esperado = 'exec sleep 5\n', 'FAIL_TIMEOUT'
    elif escenario == 'senal':
        final, esperado = 'kill -TERM $$\n', 'FAIL_EXIT'
    elif escenario in opciones_invalidas or escenario in ['ejecutable_ausente', 'programa_ausente', 'timeout_cero']:
        esperado = 'INVALID_CONFIG'
    elif escenario != 'limpio':
        raise ValueError('Escenario desconocido: ' + escenario)

    # Los fixtures no ejecutan Core ni desactivan detectores de una VM real.
    env = os.environ.copy()
    for name in ['ASAN_OPTIONS', 'UBSAN_OPTIONS', 'LSAN_OPTIONS']:
        env.pop(name, None)
    if escenario in opciones_invalidas:
        name, value = opciones_invalidas[escenario]
        env[name] = value
    with tempfile.TemporaryDirectory(prefix='mictlan p03 ') as temporary:
        root = Path(temporary)
        executable, program = root / 'fixture.sh', root / 'entrada.mict'
        executable.write_text('#!/bin/sh\nprintf %s ' + shlex.quote(stdout) + '\nprintf %s ' + shlex.quote(stderr) + ' >&2\n' + final, encoding='utf-8')
        executable.chmod(0o700)
        program.write_text('// entrada simulada\n', encoding='utf-8')
        if escenario == 'ejecutable_ausente':
            executable.unlink()
        if escenario == 'programa_ausente':
            program.unlink()
        logs = root / 'logs'
        wrapper = Path(__file__).resolve().parents[1] / ('verificar_suma_error_' + args.caso + '.cmake')
        command = [args.cmake, '-DMICTLAN_EJECUTABLE=' + str(executable), '-DMICTLAN_PROGRAMA=' + str(program), '-DMICTLAN_LOG_DIR=' + str(logs)]
        if escenario in ['timeout', 'timeout_cero']:
            command.append('-DMICTLAN_TIMEOUT=' + ('0.1' if escenario == 'timeout' else '0'))
        command += ['-P', str(wrapper)]
        result = subprocess.run(command, cwd=root, env=env, capture_output=True, text=True, timeout=15)
        actual = (logs / 'clasificacion.txt').read_text().strip() if (logs / 'clasificacion.txt').exists() else 'MISSING_RESULT'
        correcto = actual == esperado and ((result.returncode == 0) == (esperado == 'PASS'))
        if esperado != 'INVALID_CONFIG':
            correcto = correcto and (logs / 'stdout.log').read_text() == stdout and (logs / 'stderr.log').read_text() == stderr
        print(json.dumps({'caso': args.caso, 'escenario': escenario, 'esperado': esperado, 'observado': actual, 'retorno_cmake': result.returncode}, ensure_ascii=False))
        if not correcto:
            print(result.stdout)
            print(result.stderr)
            return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

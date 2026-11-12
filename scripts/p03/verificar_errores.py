#!/usr/bin/env python3
"""Comprueba directamente tipo/rango y conserva evidencia; no compila ni edita Core.

Retornos: 0 comprobacion aprobada, 1 fallo, 2 bloqueo de infraestructura,
3 configuracion invalida. Debug solo acredita comportamiento funcional.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

SDK = Path(__file__).resolve().parents[2]


class InvalidConfig(Exception):
    pass


class ConfigParser(argparse.ArgumentParser):
    def error(self, message):
        self.print_usage(sys.stderr)
        self.exit(3, 'Configuracion invalida: ' + message + '\n')


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_cache(build):
    cache = build / 'CMakeCache.txt'
    if not cache.is_file():
        raise InvalidConfig('Falta ' + str(cache))
    values = {}
    for line in cache.read_text(encoding='utf-8').splitlines():
        if line and not line.startswith(('#', '//')) and '=' in line:
            key, value = line.split('=', 1)
            values[key.split(':', 1)[0]] = value
    return values


def git_state(source, env):
    def git(*args):
        result = subprocess.run(['git', '-C', str(source), *args], env=env, capture_output=True, timeout=15)
        if result.returncode:
            raise InvalidConfig('No se pudo identificar Git en ' + str(source))
        return result.stdout
    untracked = git('ls-files', '--others', '--exclude-standard', '-z').decode().split('\0')
    return {
        'source': str(source), 'head': git('rev-parse', 'HEAD').decode().strip(),
        'branch': git('branch', '--show-current').decode().strip(),
        'status': git('status', '--porcelain').decode(),
        'tracked_diff_sha256': hashlib.sha256(git('diff', '--binary', 'HEAD')).hexdigest(),
        'untracked_sha256': {name: sha256(source / name) for name in untracked if name and (source / name).is_file()},
    }


def strict_environment(profile):
    env = os.environ.copy()
    # Estos valores afectarian que el informe vea y rechace los diagnosticos.
    disabled = {'detect_leaks', 'leak_check_at_exit', 'halt_on_error',
                'detect_stack_use_after_return', 'alloc_dealloc_mismatch'}
    for variable in ['ASAN_OPTIONS', 'UBSAN_OPTIONS', 'LSAN_OPTIONS']:
        for option in env.get(variable, '').split(':'):
            key, separator, value = option.lower().partition('=')
            if not separator:
                if option:
                    raise InvalidConfig('Opcion no reconocida en ' + variable)
                continue
            if ((key in disabled and value in ['0', 'false']) or
                (key == 'exitcode' and re.fullmatch(r'[+]?0+', value)) or
                (key == 'start_deactivated' and value in ['1', 'true']) or
                (key == 'suppressions' and value) or
                (key == 'log_path' and value not in ['stdout', 'stderr'])):
                raise InvalidConfig(variable + ' contiene una opcion que oculta o desactiva controles')
    if profile == 'sanitizers':
        defaults = {
            'ASAN_OPTIONS': 'detect_leaks=1:halt_on_error=1:detect_stack_use_after_return=1:exitcode=86',
            'UBSAN_OPTIONS': 'halt_on_error=1:print_stacktrace=1:exitcode=86',
            'LSAN_OPTIONS': 'leak_check_at_exit=1:exitcode=86',
        }
        for key, value in defaults.items():
            # Se preservan opciones adicionales; nunca se acepta exitcode=0.
            env[key] = ':'.join(filter(None, [env.get(key), value]))
    env['GIT_OPTIONAL_LOCKS'] = '0'
    return env


def classify_lsan(clean, leak):
    text = '\n'.join(clean['streams'] + leak['streams']).lower()
    # Una fuga valida de LSan puede terminar con SUMMARY: AddressSanitizer.
    # Ese resumen no es un error ASan distinto del control positivo esperado.
    if ('error: addresssanitizer' in text or 'addresssanitizer:deadlysignal' in text or
        'runtime error:' in text or 'undefinedbehaviorsanitizer' in text):
        return 'FAIL_PREFLIGHT'
    if ('leaksanitizer has encountered a fatal error' in text or
        'leaksanitizer does not work under ptrace' in text):
        return 'BLOCKED_INFRASTRUCTURE'
    leak_text = '\n'.join(leak['streams']).lower()
    clean_text = '\n'.join(clean['streams']).lower()
    if (clean['returncode'] == 0 and 'sanitizer' not in clean_text and
        isinstance(leak['returncode'], int) and leak['returncode'] > 0 and
        'leaksanitizer: detected memory leaks' in leak_text and
        re.search(r'137 byte\(s\) leaked in 1 allocation', leak_text)):
        return 'PASS'
    return 'FAIL_PREFLIGHT'


def main():
    parser = ConfigParser(description=__doc__)
    parser.add_argument('--sdk-build', required=True, type=Path)
    parser.add_argument('--core-source', required=True, type=Path)
    parser.add_argument('--core-build', required=True, type=Path)
    parser.add_argument('--profile', choices=['debug', 'release', 'sanitizers'], required=True)
    parser.add_argument('--output', required=True, type=Path, help='Directorio nuevo, fuera de las fuentes')
    parser.add_argument('--cmake', default='cmake')
    args = parser.parse_args()
    args.sdk_build, args.core_source, args.core_build, args.output = (
        path.resolve() for path in [args.sdk_build, args.core_source, args.core_build, args.output])
    for source in [SDK, args.core_source]:
        if args.output == source or source in args.output.parents:
            parser.error('--output debe quedar fuera de los repositorios de fuentes')
    try:
        args.output.mkdir(parents=True, exist_ok=False)
    except FileExistsError:
        parser.error('--output ya existe; usar otro nombre para conservar la evidencia anterior')
    report = {'schema': 1, 'stage': 'P0.3-1', 'started_utc': datetime.now(timezone.utc).isoformat(),
              'profile': args.profile, 'scope': ['mictlan_ciencia_suma_error_tipo', 'mictlan_ciencia_suma_error_rango'],
              'commands': [], 'cases': [], 'preflight': 'NOT_RUN', 'status': 'NOT_RUN'}
    env = os.environ.copy()

    def run(name, command, timeout=30):
        command = list(map(str, command))
        start = time.monotonic()
        stdout_path, stderr_path = args.output / (name + '.stdout.log'), args.output / (name + '.stderr.log')
        with stdout_path.open('wb') as stdout, stderr_path.open('wb') as stderr:
            try:
                result = subprocess.run(command, cwd=args.output, env=env, stdout=stdout, stderr=stderr, timeout=timeout)
                returncode = result.returncode
            except subprocess.TimeoutExpired:
                returncode = 'TIMEOUT'
            except OSError as exc:
                stderr.write(str(exc).encode())
                returncode = 'EXEC_ERROR'
        row = {'name': name, 'argv': command, 'cwd': str(args.output), 'returncode': returncode,
               'seconds': round(time.monotonic() - start, 3),
               'stdout': stdout_path.name, 'stderr': stderr_path.name}
        report['commands'].append(row)
        return dict(row, streams=[stdout_path.read_text(errors='replace'), stderr_path.read_text(errors='replace')])

    exitcode = 3
    try:
        env = strict_environment(args.profile)
        report['environment'] = {key: env.get(key) for key in ['ASAN_OPTIONS', 'UBSAN_OPTIONS', 'LSAN_OPTIONS', 'CC', 'CFLAGS', 'CPATH', 'LIBRARY_PATH', 'LD_LIBRARY_PATH', 'LD_PRELOAD']}
        sdk_cache, core_cache = read_cache(args.sdk_build), read_cache(args.core_build)
        expected = [(sdk_cache, 'CMAKE_HOME_DIRECTORY', SDK),
                    (core_cache, 'CMAKE_HOME_DIRECTORY', args.core_source),
                    (sdk_cache, 'LATINO_INCLUDE_DIR', args.core_source / 'include')]
        for cache, key, path in expected:
            if key not in cache or Path(cache[key]).resolve() != path.resolve():
                raise InvalidConfig('Ruta incoherente en CMakeCache: ' + key)
        executable = args.sdk_build / 'mictlan_ciencia_consola'
        library = args.core_build / 'liblatino.so'
        if not executable.is_file() or not library.is_file():
            raise InvalidConfig('Falta compilar el ejecutor SDK o liblatino.so')
        if Path(sdk_cache.get('LATINO_LIBRARY', '')).resolve() != library.resolve():
            raise InvalidConfig('LATINO_LIBRARY no corresponde al Core seleccionado')
        cmake = shutil.which(args.cmake)
        if not cmake:
            raise InvalidConfig('No se encontro CMake')
        compiler = core_cache.get('CMAKE_C_COMPILER')
        if not compiler or not Path(compiler).is_file():
            raise InvalidConfig('No se encontro el compilador registrado por Core')
        report['sources'] = {'sdk': git_state(SDK, env), 'core': git_state(args.core_source, env)}
        report['source_binary_binding'] = 'Rutas de CMake verificadas; el usuario suministra los builds. No se recompila Core ni se acredita frescura solo por timestamps.'
        report['binaries'] = {str(path): sha256(path) for path in [executable, library]}
        report['headers'] = {path.name: sha256(path) for path in sorted((args.core_source / 'include').glob('*.h'))}
        report['cache_sha256'] = {str(build / 'CMakeCache.txt'): sha256(build / 'CMakeCache.txt')
                                  for build in [args.sdk_build, args.core_build]}
        report['cache'] = {name: {key: value for key, value in cache.items() if key.startswith(('CMAKE_C_', 'CMAKE_BUILD_TYPE', 'CMAKE_EXE_LINKER_FLAGS', 'CMAKE_SHARED_LINKER_FLAGS', 'LATINO_', 'raylib_DIR'))}
                           for name, cache in [('sdk', sdk_cache), ('core', core_cache)]}
        report['platform'] = {'sys_platform': sys.platform, 'machine': os.uname().machine}
        for name, command in [('cmake-version', [cmake, '--version']), ('compiler-version', [compiler, '--version'])]:
            if run(name, command)['returncode'] != 0:
                raise InvalidConfig('No se pudo registrar ' + name)
        loader = run('loaded-libraries', ['ldd', str(executable)])
        match = re.search(r'^\s*liblatino\.so => (.*?) \(', loader['streams'][0], re.MULTILINE)
        if loader['returncode'] != 0 or not match or Path(match.group(1)).resolve() != library.resolve():
            raise InvalidConfig('El cargador no resuelve la biblioteca Core seleccionada')

        if args.profile == 'sanitizers':
            for name, binary in [('sdk', executable), ('core', library)]:
                symbols = run('instrumentation-' + name, ['nm', '-D', str(binary)])
                if symbols['returncode'] != 0 or not all(marker in symbols['streams'][0] for marker in ['__asan_', '__ubsan_']):
                    raise InvalidConfig('No se acredita instrumentacion ASan/UBSan en ' + name)
            control = args.output / 'lsan_control'
            compiled = run('preflight-build', [compiler, '-g', '-O0', '-fsanitize=address,undefined',
                           '-fno-sanitize-recover=undefined', '-fno-omit-frame-pointer',
                           SDK / 'tests/p03/lsan_control.c', '-o', control])
            if compiled['returncode'] != 0:
                raise InvalidConfig('No se pudo compilar el control independiente de LSan')
            report['preflight'] = classify_lsan(run('preflight-clean', [control]), run('preflight-leak', [control, 'leak']))
        else:
            report['preflight'] = 'NOT_APPLICABLE_FUNCTIONAL'

        for case in ['tipo', 'rango']:
            logs = args.output / case
            result = run('verifier-' + case, [cmake, '-DMICTLAN_EJECUTABLE=' + str(executable),
                         '-DMICTLAN_PROGRAMA=' + str(SDK / 'tests/datos' / ('mictlan_suma_error_' + case + '.mict')),
                         '-DMICTLAN_LOG_DIR=' + str(logs), '-P', SDK / 'tests' / ('verificar_suma_error_' + case + '.cmake')])
            classification_file = logs / 'clasificacion.txt'
            classification = classification_file.read_text().strip() if classification_file.is_file() else 'FAIL_MISSING_RESULT'
            if classification == 'PASS' and result['returncode'] != 0:
                classification = 'FAIL_WRAPPER'
            report['cases'].append({'name': 'mictlan_ciencia_suma_error_' + case,
                                    'status': classification, 'wrapper_returncode': result['returncode'],
                                    'program_returncode': (logs / 'estado.txt').read_text().strip() if (logs / 'estado.txt').exists() else None,
                                    'logs': case + '/'})
        # P0.2 puede trabajar a la vez: rechazar una corrida con entradas moviles.
        report['inputs_unchanged'] = (
            report['sources'] == {'sdk': git_state(SDK, env), 'core': git_state(args.core_source, env)} and
            report['binaries'] == {str(path): sha256(path) for path in [executable, library]} and
            report['headers'] == {path.name: sha256(path) for path in sorted((args.core_source / 'include').glob('*.h'))} and
            all(sha256(path) == digest for path, digest in report['cache_sha256'].items()))
        if not report['inputs_unchanged']:
            raise InvalidConfig('Las fuentes, cabeceras, bibliotecas o caches cambiaron durante la comprobacion')
        statuses = [item['status'] for item in report['cases']]
        if report['preflight'] == 'FAIL_PREFLIGHT' or any(status not in ['PASS', 'BLOCKED_INFRASTRUCTURE'] for status in statuses):
            report['status'], exitcode = 'FAIL', 1
        elif report['preflight'] == 'BLOCKED_INFRASTRUCTURE' or 'BLOCKED_INFRASTRUCTURE' in statuses:
            report['status'], exitcode = 'BLOCKED_INFRASTRUCTURE', 2
        else:
            report['status'], exitcode = ('PASS_SANITIZERS' if args.profile == 'sanitizers' else 'PASS_FUNCTIONAL'), 0
    except (InvalidConfig, OSError, ValueError, subprocess.TimeoutExpired) as exc:
        report['status'], report['error'], exitcode = 'INVALID_CONFIG', str(exc), 3
    finally:
        report['finished_utc'] = datetime.now(timezone.utc).isoformat()
        report['exitcode'] = exitcode
        (args.output / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        lines = ['# Mictlan P0.3-1: comprobacion directa de errores', '',
                 '**Estado:** ' + report['status'], '**Perfil:** ' + args.profile,
                 '**Control LSan:** ' + report['preflight'], '',
                 'Debug acredita comportamiento funcional; las simulaciones no acreditan memoria del Core.', '',
                 '| Prueba | Clasificacion | Retorno del programa |', '|---|---|---|']
        for item in report['cases']:
            lines.append('| ' + item['name'] + ' | ' + item['status'] + ' | ' + str(item['program_returncode']) + ' |')
        if 'error' in report:
            lines.extend(['', 'Configuracion rechazada: ' + report['error']])
        lines.extend(['', 'SHAs, estado de los arboles, hashes, opciones efectivas y comandos: `report.json`.',
                      'Una comprobacion bloqueada no se convierte en aprobacion aunque otros casos pasen.', ''])
        (args.output / 'report.md').write_text('\n'.join(lines), encoding='utf-8')
    print(report['status'] + ': ' + str(args.output / 'report.json'))
    return exitcode


if __name__ == '__main__':
    raise SystemExit(main())

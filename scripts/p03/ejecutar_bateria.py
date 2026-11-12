#!/usr/bin/env python3
"""Bateria P0.3-2. Retornos: 0 aprobada, 1 fallo, 2 infraestructura, 3 configuracion.

No compila ni modifica Core. Requiere builds separados y conserva resultados sin
sobrescribir. CI prepara builds nuevos; uso local registra el arbol pendiente.
"""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

sys.dont_write_bytecode = True
from verificar_errores import (ConfigParser, InvalidConfig, SDK, git_state, read_cache,
                              sha256, strict_environment)


INFRA = re.compile(r'LeakSanitizer (?:has encountered a fatal error|does not work under ptrace)', re.I)
SANITIZER = re.compile(r'AddressSanitizer|UndefinedBehaviorSanitizer|LeakSanitizer: detected memory leaks|runtime error:|\b(?:asan|ubsan|lsan)\s*:', re.I)


def classify_case(text, failed, skipped=False):
    # Un fallo real tiene prioridad, aunque tambien haya bloqueo de LSan.
    if SANITIZER.search(text):
        return 'FAIL_SANITIZER'
    if re.search(r'"(?:ok"\s*:\s*false|status"\s*:\s*"FAIL")', text):
        return 'FAIL_PROGRAM'
    if INFRA.search(text):
        return 'BLOCKED_INFRASTRUCTURE'
    if re.search(r'sanitizer', text, re.I):
        return 'FAIL_SANITIZER'
    if skipped:
        return 'FAIL_NOT_RUN'
    return 'FAIL_PROGRAM' if failed else 'PASS'


def classify_suite(xml_path, returncode, expected_count, scan_sanitizers=True):
    try:
        root = ET.parse(xml_path).getroot()
        cases = root.findall('.//testcase')
        if len(cases) != expected_count:
            return {'status': 'FAIL_TEST_COUNT', 'expected': expected_count, 'actual': len(cases)}
        rows = []
        for case in cases:
            failed = case.find('failure') is not None or case.find('error') is not None
            skipped = case.find('skipped') is not None or case.get('status') in ['notrun', 'disabled']
            text = ''.join(case.itertext())
            status = classify_case(text, failed, skipped) if scan_sanitizers else (
                'FAIL_NOT_RUN' if skipped else 'FAIL_PROGRAM' if failed else 'PASS')
            if 'test output was removed since it exceeds' in text:
                status = 'FAIL_OUTPUT_TRUNCATED'
            rows.append({'name': case.get('name'), 'status': status})
        if any(not row['name'] for row in rows) or len({row['name'] for row in rows}) != expected_count:
            return {'status': 'FAIL_TEST_COUNT', 'error': 'Nombres repetidos', 'cases': rows}
        if any(row['status'].startswith('FAIL') for row in rows):
            status = 'FAIL'
        elif any(row['status'] == 'BLOCKED_INFRASTRUCTURE' for row in rows):
            status = 'BLOCKED_INFRASTRUCTURE'
        else:
            status = 'PASS' if returncode == 0 else 'FAIL_CTEST'
        return {'status': status, 'cases': rows, 'returncode': returncode}
    except (ET.ParseError, OSError) as exc:
        return {'status': 'FAIL_MISSING_JUNIT', 'error': str(exc)}


def aggregate(statuses):
    allowed = {'PASS', 'PASS_FUNCTIONAL', 'PASS_SANITIZERS', 'BLOCKED_INFRASTRUCTURE'}
    if not statuses or any(status not in allowed for status in statuses):
        return 'FAIL', 1
    if 'BLOCKED_INFRASTRUCTURE' in statuses:
        return 'BLOCKED_INFRASTRUCTURE', 2
    return 'PASS', 0


def is_elf(path):
    if not path.is_file():
        return False
    with path.open('rb') as stream:
        return stream.read(4) == b'\x7fELF'


def main():
    parser = ConfigParser(description=__doc__)
    for name in ['sdk-build', 'core-source', 'core-build', 'vm-build', 'verifiers-build', 'output']:
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--profile', choices=['debug', 'sanitizers'], required=True)
    parser.add_argument('--expected-sdk-sha', required=True)
    parser.add_argument('--allow-sdk-dirty', action='store_true', help='Solo revision local; CI exige arbol limpio')
    parser.add_argument('--cmake', default='cmake')
    parser.add_argument('--ctest', default='ctest')
    args = parser.parse_args()
    for name in ['sdk_build', 'core_source', 'core_build', 'vm_build', 'verifiers_build', 'output']:
        setattr(args, name, getattr(args, name).resolve())
    for source in [SDK, args.core_source]:
        if args.output == source or source in args.output.parents:
            parser.error('--output debe quedar fuera de las fuentes')
    try:
        args.output.mkdir(parents=True, exist_ok=False)
    except FileExistsError:
        parser.error('--output ya existe; no se sobrescribe evidencia')
    report = {'schema': 1, 'stage': 'P0.3-2', 'started_utc': datetime.now(timezone.utc).isoformat(),
              'profile': args.profile, 'commands': [], 'checks': {}, 'status': 'INVALID_CONFIG'}
    env = os.environ.copy()

    def run(name, argv, timeout=120):
        argv = list(map(str, argv))
        start = time.monotonic()
        stdout, stderr = args.output / (name + '.stdout.log'), args.output / (name + '.stderr.log')
        with stdout.open('wb') as out, stderr.open('wb') as err:
            try:
                code = subprocess.run(argv, cwd=args.output, env=env, stdout=out, stderr=err, timeout=timeout).returncode
            except subprocess.TimeoutExpired:
                code = 'TIMEOUT'
            except OSError as exc:
                err.write(str(exc).encode()); code = 'EXEC_ERROR'
        report['commands'].append({'name': name, 'argv': argv, 'returncode': code,
                                   'seconds': round(time.monotonic() - start, 3),
                                   'stdout': stdout.name, 'stderr': stderr.name})
        return code, stdout.read_text(errors='replace'), stderr.read_text(errors='replace')

    exitcode = 3
    try:
        env = strict_environment(args.profile)
        lock = json.loads((SDK / 'ci/p03/contrato.json').read_text())
        report['contract'] = lock
        report['environment'] = {key: env.get(key) for key in ['ASAN_OPTIONS', 'UBSAN_OPTIONS', 'LSAN_OPTIONS', 'CPATH', 'LIBRARY_PATH', 'LD_LIBRARY_PATH', 'LD_PRELOAD']}
        sources = {'sdk': git_state(SDK, env), 'core': git_state(args.core_source, env)}
        report['sources'] = sources
        if sources['core']['head'] != lock['core_sha'] or sources['core']['status']:
            raise InvalidConfig('Core debe ser el SHA limpio fijado en contrato.json')
        if not re.fullmatch(r'[0-9a-f]{40}', args.expected_sdk_sha) or sources['sdk']['head'] != args.expected_sdk_sha:
            raise InvalidConfig('El SHA exacto del SDK no coincide con el solicitado')
        if sources['sdk']['status'] and not args.allow_sdk_dirty:
            raise InvalidConfig('SDK con cambios pendientes: CI requiere commit limpio')
        report['identity'] = 'WORKTREE_REVIEW' if sources['sdk']['status'] else 'EXACT_COMMIT_PAIR'
        if run('sdk-base', ['git', '-C', SDK, 'merge-base', '--is-ancestor', lock['sdk_base_sha'], 'HEAD'])[0]:
            raise InvalidConfig('El SDK no deriva de la base aprobada')
        if platform.system() != 'Linux' or platform.machine() != 'x86_64':
            raise InvalidConfig('Este contrato ABI inicial solo cubre Linux x86_64')
        caches = {name: read_cache(build) for name, build in [
            ('sdk', args.sdk_build), ('core', args.core_build), ('vm', args.vm_build), ('verifiers', args.verifiers_build)]}
        source_paths = {'sdk': SDK, 'core': args.core_source, 'vm': SDK / 'tests/p03_vm', 'verifiers': SDK / 'tests/p03'}
        library = args.core_build / 'liblatino.so'
        inputs = [library, args.sdk_build / 'mictlan_ciencia_consola', args.vm_build / 'p03_vm_recuperacion']
        inputs += list((args.core_source / 'include').glob('*.h'))
        inputs += [build / 'CMakeCache.txt' for build in [args.sdk_build, args.core_build, args.vm_build, args.verifiers_build]]
        report['input_hashes'] = {str(path): sha256(path) for path in inputs}
        for name, cache in caches.items():
            if Path(cache['CMAKE_HOME_DIRECTORY']).resolve() != source_paths[name]:
                raise InvalidConfig('CMake source incorrecto: ' + name)
            if name != 'verifiers' and cache.get('CMAKE_BUILD_TYPE') != 'Debug':
                raise InvalidConfig('Se requiere Debug, tambien con sanitizadores: ' + name)
            if name in ['sdk', 'vm']:
                if (Path(cache.get('LATINO_LIBRARY', '')).resolve() != library or
                    Path(cache.get('LATINO_INCLUDE_DIR', '')).resolve() != args.core_source / 'include'):
                    raise InvalidConfig('Biblioteca/cabeceras incoherentes: ' + name)
        report['caches'] = {name: {key: val for key, val in cache.items() if key.startswith(('CMAKE_C_', 'CMAKE_BUILD_TYPE', 'CMAKE_EXE_LINKER_FLAGS', 'CMAKE_SHARED_LINKER_FLAGS', 'LATINO_', 'raylib_DIR'))} for name, cache in caches.items()}
        for name, command in [('cmake-version', [args.cmake, '--version']), ('ctest-version', [args.ctest, '--version']),
                              ('compiler-version', [caches['core']['CMAKE_C_COMPILER'], '--version']),
                              ('platform', ['uname', '-a'])]:
            rc, output, _ = run(name, command)
            if rc: raise InvalidConfig('No se pudo registrar ' + name)
            if name in ['cmake-version', 'ctest-version']:
                version = re.search(r'version (\d+)\.(\d+)', output)
                if not version or tuple(map(int, version.groups())) < (3, 26):
                    raise InvalidConfig('CMake y CTest deben ser >= 3.26')
        # Exportaciones y todos los consumidores ELF situados en la raiz del build SDK.
        rc, symbols, _ = run('core-exports', ['nm', '-D', '--defined-only', library])
        exports = {line.split()[-1].split('@')[0] for line in symbols.splitlines() if line.split()}
        missing = set(lock['required_exports']) - exports
        if rc or missing: raise InvalidConfig('Exportaciones ausentes: ' + ', '.join(sorted(missing)))
        consumers = [path for path in sorted(args.sdk_build.iterdir()) if is_elf(path)]
        consumers.append(args.vm_build / 'p03_vm_recuperacion')
        inputs.extend(path for path in consumers if path not in inputs)
        report['input_hashes'].update({str(path): sha256(path) for path in consumers})
        imports = set()
        linked = []
        for index, binary in enumerate(consumers):
            rc, symbols, _ = run('imports-' + str(index), ['nm', '-D', '--undefined-only', binary])
            if rc: raise InvalidConfig('No se pudieron revisar simbolos: ' + str(binary))
            names = {line.split()[-1].split('@')[0] for line in symbols.splitlines() if line.split()}
            needed = {name for name in names if re.match(r'^lat[A-Z_]', name)}
            imports.update(needed)
            if needed:
                rc, loader, loader_err = run('loader-' + str(index), ['ldd', '-r', binary])
                match = re.search(r'liblatino\.so => (.*?) \(', loader)
                if rc or 'undefined symbol:' in loader + loader_err or not match or Path(match.group(1)).resolve() != library:
                    raise InvalidConfig('Enlace Core incorrecto: ' + str(binary))
                linked.append(str(binary))
        if imports - exports: raise InvalidConfig('Importaciones lat* sin resolver')
        # El layout es una huella de cabeceras; no sustituye un comparador ABI completo.
        probe = args.output / 'abi_contract'
        if run('abi-compile', [caches['sdk']['CMAKE_C_COMPILER'], '-std=c11', '-I' + str(args.core_source / 'include'), SDK / 'ci/p03/abi_contract.c', '-o', probe])[0]:
            raise InvalidConfig('No se pudo compilar la huella ABI')
        rc, layout, _ = run('abi-layout', [probe])
        report['abi'] = {'layout': json.loads(layout), 'exports_count': len(exports),
                         'sdk_imports': sorted(imports), 'linked_consumers': linked,
                         'scope': 'Simbolos, cargador y layout de cabeceras; no certificacion de toda la ABI'}
        if rc or report['abi']['layout'] != lock['abi_linux_x86_64']:
            raise InvalidConfig('El layout publico no coincide con el contrato revisado')
        report['checks']['contract'] = {'status': 'PASS'}
        if args.profile == 'sanitizers':
            for name, binary in [('core', library), ('sdk', inputs[1]), ('vm', inputs[2])]:
                rc, output, _ = run('instrumentation-' + name, ['nm', '-D', binary])
                if rc or not all(marker in output for marker in ['__asan_', '__ubsan_']):
                    raise InvalidConfig('Falta instrumentacion ASan/UBSan: ' + name)
            control = args.output / 'sanitizer_control'
            if run('sanitizer-control-build', [caches['core']['CMAKE_C_COMPILER'], '-g', '-O0',
                '-fsanitize=address,undefined', '-fno-sanitize-recover=all', '-fno-omit-frame-pointer',
                SDK / 'ci/p03/sanitizer_control.c', '-o', control])[0]:
                raise InvalidConfig('No se pudo compilar el control positivo ASan/UBSan')
            asan = run('asan-positive', [control, 'asan'])
            ubsan = run('ubsan-positive', [control, 'ubsan'])
            positive = (asan[0] == 86 and 'ERROR: AddressSanitizer: heap-buffer-overflow' in asan[1] + asan[2] and
                        ubsan[0] == 86 and 'runtime error: signed integer overflow' in ubsan[1] + ubsan[2])
            report['checks']['sanitizer_runtime'] = {'status': 'PASS' if positive else 'FAIL_PREFLIGHT',
                                                      'asan_returncode': asan[0], 'ubsan_returncode': ubsan[0]}
        rc, _, _ = run('direct-errors', [sys.executable, SDK / 'scripts/p03/verificar_errores.py',
            '--sdk-build', args.sdk_build, '--core-source', args.core_source, '--core-build', args.core_build,
            '--profile', args.profile, '--output', args.output / 'direct-errors', '--cmake', args.cmake])
        direct = json.loads((args.output / 'direct-errors/report.json').read_text())
        report['checks']['direct_errors'] = {'status': direct['status'], 'returncode': rc, 'preflight': direct['preflight']}
        if rc != direct['exitcode']: raise InvalidConfig('Retorno incoherente del verificador directo')
        if rc == 3: raise InvalidConfig('Verificador directo rechazo la configuracion: ' + direct.get('error', 'sin detalle'))
        for name, build in [('verifiers', args.verifiers_build), ('sdk', args.sdk_build), ('vm', args.vm_build)]:
            rc, listing, _ = run('list-' + name, [args.ctest, '--test-dir', build, '--show-only=json-v1'])
            tests = json.loads(listing)['tests'] if rc == 0 else []
            if len(tests) != lock['test_counts'][name]: raise InvalidConfig('Inventario CTest inesperado: ' + name)
            for test in tests:
                for prop in test.get('properties', []):
                    if prop['name'] in ['WILL_FAIL', 'DISABLED', 'SKIP_RETURN_CODE', 'SKIP_REGULAR_EXPRESSION', 'ENVIRONMENT', 'ENVIRONMENT_MODIFICATION'] and prop['value']:
                        raise InvalidConfig('Propiedad CTest que cambia el contrato: ' + test['name'] + '/' + prop['name'])
            junit = args.output / (name + '.xml')
            rc, _, _ = run('ctest-' + name, [args.ctest, '--test-dir', build, '--no-tests=error', '-V',
                '--timeout', '60', '--test-output-size-passed', '16777216',
                '--test-output-size-failed', '16777216', '--output-junit', junit], timeout=600)
            # La suite de fixtures contiene informes falsos intencionalmente.
            report['checks'][name] = classify_suite(junit, rc, lock['test_counts'][name], name != 'verifiers')
            result_names = {row['name'] for row in report['checks'][name].get('cases', [])}
            if result_names != {test['name'] for test in tests}:
                report['checks'][name]['status'] = 'FAIL_TEST_INVENTORY'
        report['inputs_unchanged'] = (report['input_hashes'] == {str(path): sha256(path) for path in inputs} and
            sources == {'sdk': git_state(SDK, env), 'core': git_state(args.core_source, env)})
        if not report['inputs_unchanged']: raise InvalidConfig('Fuentes o binarios cambiaron durante la ejecucion')
        report['status'], exitcode = aggregate([row['status'] for row in report['checks'].values()])
    except (InvalidConfig, OSError, ValueError, KeyError, subprocess.TimeoutExpired) as exc:
        report['status'], report['error'], exitcode = 'INVALID_CONFIG', str(exc), 3
    finally:
        report['exitcode'] = exitcode
        report['finished_utc'] = datetime.now(timezone.utc).isoformat()
        (args.output / 'report.json').write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
        suite = ET.Element('testsuite', name='P0.3-2-summary')
        for name, data in {**report['checks'], 'overall': {'status': report['status']}}.items():
            case = ET.SubElement(suite, 'testcase', name=name)
            if not data['status'].startswith('PASS'):
                tag = 'error' if data['status'] in ['BLOCKED_INFRASTRUCTURE', 'INVALID_CONFIG'] else 'failure'
                ET.SubElement(case, tag, message=data['status']).text = json.dumps(data)
        ET.ElementTree(suite).write(args.output / 'summary.xml', encoding='utf-8', xml_declaration=True)
    print(report['status'] + ': ' + str(args.output / 'report.json'))
    return exitcode


if __name__ == '__main__':
    raise SystemExit(main())

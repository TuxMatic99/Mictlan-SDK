"""Ejecutar inventario Core sin heredar propiedades que desactivan LSan.

No modifica sus fuentes ni genera pruebas ficticias: conserva argv, directorio,
limite y propiedades originales. Todos los fallos afectan el resultado global.
"""
import json
import hashlib
from pathlib import Path
import xml.etree.ElementTree as ET


def validate_inventory(tests, expected):
    if len(tests) != expected or len({t['name'] for t in tests}) != expected:
        raise ValueError('Inventario Core inesperado')
    for test in tests:
        props = {p['name']: p['value'] for p in test.get('properties', [])}
        for key in ['WILL_FAIL', 'DISABLED', 'SKIP_RETURN_CODE', 'SKIP_REGULAR_EXPRESSION', 'ENVIRONMENT_MODIFICATION']:
            if props.get(key):
                raise ValueError('Propiedad que oculta resultados: ' + test['name'] + '/' + key)
        for value in props.get('ENVIRONMENT', []):
            if value.split('=', 1)[0] not in ['ASAN_OPTIONS', 'UBSAN_OPTIONS', 'LSAN_OPTIONS']:
                raise ValueError('Entorno Core sin revisar: ' + value)


def run_core(run, ctest, core, build, output, expected, classify, aggregate, known):
    rc, text, _ = run('core-inventory', [ctest, '--test-dir', build, '--show-only=json-v1'])
    if rc: raise ValueError('No se pudo enumerar Core')
    tests = json.loads(text)['tests']
    validate_inventory(tests, expected)
    rows = []
    suite = ET.Element('testsuite', name='core-strict')
    for test in tests:
        props = {p['name']: p['value'] for p in test.get('properties', [])}
        rc, stdout, stderr = run('core-' + test['name'], test['command'],
            timeout=props.get('TIMEOUT', 60), cwd=props.get('WORKING_DIRECTORY', build))
        status = classify(stdout + stderr, rc != 0)
        # LSan puede finalizar antes de vaciar stdout: no perder el error de
        # configuracion conocido aunque desaparezca el mensaje del interprete.
        missing_coverage = test['name'] == 'coverage' and not (
            Path(props.get('WORKING_DIRECTORY', build)) / test['command'][-1]).is_file()
        if missing_coverage:
            status = 'FAIL_CONFIGURATION'
        rows.append({'name': test['name'], 'status': status, 'returncode': rc,
                     'missing_coverage_input': missing_coverage,
                     'known_failure': test['name'] in known, 'original_properties': props,
                     'effective_environment': 'Strict parent environment; original sanitizer overrides not applied'})
        case = ET.SubElement(suite, 'testcase', name=test['name'])
        if status != 'PASS':
            ET.SubElement(case, 'error' if status == 'BLOCKED_INFRASTRUCTURE' else 'failure', message=status)
        ET.SubElement(case, 'system-out').text = stdout
        ET.SubElement(case, 'system-err').text = stderr
    ET.ElementTree(suite).write(output / 'core.xml', encoding='utf-8', xml_declaration=True)
    return {'status': aggregate([r['status'] for r in rows])[0], 'cases': rows}


def run_modular(run, core, build, output, classify, aggregate):
    names = ['atomic_io', 'bytecode', 'constants', 'context', 'ffi', 'hash',
             'label', 'modules', 'object_text', 'strings_io', 'system']
    rows = []
    for name in names:
        rc, out, err = run('modular-' + name, ['bash', core / 'tests' / ('run_' + name + '_regression.sh')], timeout=300)
        rows.append({'name': name, 'status': classify(out + err, rc != 0), 'returncode': rc})
    # El script historico exige ../build-core-debug. Copiar SOLO el script,
    # byte por byte: un symlink a la raiz Core haria que '..' escapase a su
    # directorio real y podria ejecutar por accidente otro build Debug.
    layout = output / 'extension-layout'
    (layout / 'core/tests').mkdir(parents=True)
    script = layout / 'core/tests/run_extension_regression.sh'
    script.write_bytes((core / 'tests/run_extension_regression.sh').read_bytes())
    (layout / 'core/ejemplos').symlink_to(core / 'ejemplos', target_is_directory=True)
    (layout / 'build-core-debug').symlink_to(build, target_is_directory=True)
    try:
        rc, out, err = run('modular-extension', ['bash', script])
    finally:
        script.unlink()
        (layout / 'core/tests').rmdir()
        (layout / 'core/ejemplos').unlink()
        (layout / 'core').rmdir()
        (layout / 'build-core-debug').unlink()
        layout.rmdir()
    rows.append({'name': 'extension', 'status': classify(out + err, rc != 0), 'returncode': rc,
                 'script_sha256': hashlib.sha256((core / 'tests/run_extension_regression.sh').read_bytes()).hexdigest(),
                 'selected_binary_sha256': hashlib.sha256((build / 'mictlan').read_bytes()).hexdigest()})
    return {'status': aggregate([r['status'] for r in rows])[0], 'cases': rows}


def run_extensions(run, core, build, output, classify, aggregate):
    # Revisar tambien las salidas crudas: el script antiguo no imprime stderr
    # en cada caso negativo que considera correcto.
    directory = output / 'extension-inputs'
    directory.mkdir()
    data = (core / 'ejemplos/hola_mictlan.lat').read_bytes()
    cases = [('hello.mict', 0, 'El resultado es: 42'), ('hello.lat', 0, 'El resultado es: 42'),
             ('hello.txt', 1, 'debe tener extension .mict o .lat'),
             ('hello', 1, 'debe tener extension .mict o .lat'),
             ('missing.mict', 1, 'No se pudo abrir el archivo')]
    rows = []
    for index, (name, expected, diagnostic) in enumerate(cases):
        path = directory / name
        if name != 'missing.mict': path.write_bytes(data)
        rc, out, err = run('extension-raw-' + str(index), [build / 'mictlan', path])
        # Los errores de CLI esperados se reconocen antes de clasificar el
        # programa, pero los sanitizadores y bloqueos tienen prioridad.
        matches = rc == expected and diagnostic in out + err
        classification_text = out + err
        if expected == 1:
            classification_text = classification_text.replace(diagnostic, 'EXPECTED_CLI_DIAGNOSTIC')
        status = classify(classification_text, not matches)
        rows.append({'name': name, 'status': status, 'returncode': rc, 'expected': expected})
    return {'status': aggregate([r['status'] for r in rows])[0], 'cases': rows}

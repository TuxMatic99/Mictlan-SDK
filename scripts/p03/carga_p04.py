"""Comparar la misma carga binaria contra F+E y P0.2-G."""
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

from verificar_errores import InvalidConfig, read_cache, sha256


def exports_de(run, label, library):
    rc, text, _ = run(label, ['nm', '-D', '--defined-only', library])
    exports = {line.split()[-1].split('@')[0] for line in text.splitlines() if line.split()}
    if rc or not exports:
        raise InvalidConfig('No se pudieron leer los símbolos de ' + str(library))
    return exports


def run_stress(run, args, lock, revision, exports, classify, aggregate):
    binary = (args.stress_build / 'p04_carga').resolve()
    old_consumer = (args.stress_build / 'p04_sdk_anterior').resolve()
    candidate = args.core_build.resolve()
    base = args.comparison_core_build.resolve()
    base_source = Path(read_cache(base)['CMAKE_HOME_DIRECTORY'])
    rc, sha, _ = run('stress-base-sha', ['git', '-C', base_source, 'rev-parse', 'HEAD'])
    if rc or sha.strip() != lock['core_revisions'][revision['stress']['base']]['sha']:
        raise InvalidConfig('Core base de la carga no coincide con el contrato')
    rc, dirty, _ = run('stress-base-status', ['git', '-C', base_source, 'status', '--porcelain'])
    if rc or dirty.strip():
        raise InvalidConfig('La base de la carga debe estar limpia')
    base_library = base / 'liblatino.so'
    paths = {p: sha256(p) for p in [binary, old_consumer, base_library, candidate / 'liblatino.so']}
    base_exports = exports_de(run, 'p04-base-exports', base_library)
    removed, added = base_exports - exports, exports - base_exports
    if removed or added != set(revision['added_exports']):
        raise InvalidConfig('Cambios inesperados en las exportaciones de Core')
    prior_abi = None
    prior_key = revision['stress'].get('abi_previa')
    if prior_key:
        prior = args.prior_core_build.resolve()
        prior_source = Path(read_cache(prior)['CMAKE_HOME_DIRECTORY'])
        rc, prior_sha, _ = run('p04-prior-sha', ['git', '-C', prior_source, 'rev-parse', 'HEAD'])
        if rc or prior_sha.strip() != lock['core_revisions'][prior_key]['sha']:
            raise InvalidConfig('Revisión de ABI previa incorrecta')
        rc, dirty, _ = run('p04-prior-status', ['git', '-C', prior_source, 'status', '--porcelain'])
        if rc or dirty.strip():
            raise InvalidConfig('La ABI previa requiere un árbol limpio')
        prior_library = prior / 'liblatino.so'
        paths[prior_library] = sha256(prior_library)
        prior_exports = exports_de(run, 'p04-prior-exports', prior_library)
        prior_added = exports - prior_exports
        if prior_exports - exports or prior_added != set(revision['stress'].get('abi_agregados', [])):
            raise InvalidConfig('Cambio inesperado respecto de la ABI previa')
        prior_abi = {'sha': prior_sha.strip(), 'exports': len(prior_exports),
                     'equal': not prior_added, 'added': sorted(prior_added)}
    modes = [('fe', base, 'base'), ('g-sin', candidate, 'base'),
             ('g', candidate, 'recolectar')]
    for binary_name, executable in [('stress', binary), ('sdk-anterior', old_consumer)]:
        for label, library in [('fe', base), ('g', candidate)]:
            rc, out, err = run(f'{binary_name}-loader-{label}', ['ldd', '-r', executable], library=library)
            match = re.search(r'liblatino\.so => (.*?) \(', out)
            if rc or 'undefined symbol:' in out + err or not match or Path(match[1]).resolve() != library / 'liblatino.so':
                raise InvalidConfig(f'Biblioteca incorrecta: {binary_name}/{label}')
    if args.profile == 'sanitizers':
        for name, path in [('harness', binary), ('baseline', base_library), ('sdk-anterior', old_consumer)]:
            rc, out, _ = run('stress-instrumentation-' + name, ['nm', '-D', path])
            if rc or not all(mark in out for mark in ('__asan_', '__ubsan_')):
                raise InvalidConfig('Carga sin instrumentacion: ' + name)
    rows = []
    compatibility = []
    suite = ET.Element('testsuite', name='p04-carga')
    alias_program = Path(__file__).resolve().parents[2] / 'tests/datos/mictlan_alias_vector_ffi.mict'
    expected = ('=== ALIAS VECTOR FFI ===', 'Valor desde original:', '99',
                'Valor conservado por alias:', '99', 'Valor de la nueva lista:', '7',
                'Segundo componente del alias:', '77', '=== FIN ===')
    for name, library in [('fe', base), ('g', candidate)]:
        label = 'sdk-anterior-' + name
        rc, out, err = run(label, [old_consumer, alias_program], library=library)
        status = classify(out + err, rc != 0)
        if status == 'PASS' and tuple(out.splitlines()) != expected:
            status = 'FAIL_PROGRAM'
        compatibility.append({'name': label, 'status': status, 'returncode': rc})
        add_result(suite, label, status, out, err)
    sizes = (1000, 10000, 100000) if args.profile == 'release' else (1000, 10000)
    for name, library, mode in modes:
        for size in sizes:
            label = f'stress-{name}-{size}'
            rc, out, err = run(label, [binary, mode, str(size)], timeout=180, library=library)
            status = classify(out + err, rc != 0)
            try:
                samples = [json.loads(line) for line in out.splitlines()]
                if status == 'PASS' and (samples[-1]['operaciones'] != size or
                   (mode == 'recolectar' and samples[-1]['reservas_recuperadas'] <= 0)):
                    status = 'FAIL_PROGRAM'
            except (ValueError, IndexError, KeyError):
                samples = []
                if status == 'PASS':
                    status = 'FAIL_PROGRAM'
            rows.append({'name': label, 'status': status, 'returncode': rc, 'samples': samples})
            add_result(suite, label, status, out, err)
    duration = revision['stress'].get('release_seconds')
    if args.profile == 'release' and duration:
        label = 'stress-g-sesion'
        rc, out, err = run(label, [binary, 'recolectar', '10000000', str(duration)],
                           timeout=duration + 60, library=candidate)
        status = classify(out + err, rc != 0)
        try:
            samples = [json.loads(line) for line in out.splitlines()]
            if status == 'PASS' and (samples[-1]['segundos'] < duration or
               samples[-1]['reservas_recuperadas'] <= 0 or samples[-1]['operaciones'] < 100000):
                status = 'FAIL_PROGRAM'
        except (ValueError, IndexError, KeyError):
            samples = []
            if status == 'PASS':
                status = 'FAIL_PROGRAM'
        rows.append({'name': label, 'status': status, 'returncode': rc, 'samples': samples})
        add_result(suite, label, status, out, err)
    if any(sha256(p) != digest for p, digest in paths.items()):
        raise InvalidConfig('Cambio un binario durante la carga')
    ET.ElementTree(suite).write(args.output / 'stress.xml', encoding='utf-8', xml_declaration=True)
    return {'status': aggregate([r['status'] for r in rows + compatibility])[0],
            'cases': rows, 'old_consumer': compatibility, 'base_sha': sha.strip(),
            'exports': {'base_count': len(base_exports), 'added': sorted(added), 'removed': sorted(removed),
                        'prior': prior_abi},
            'hashes': {str(p): h for p, h in paths.items()}}


def add_result(suite, label, status, out, err):
    case = ET.SubElement(suite, 'testcase', name=label)
    if status != 'PASS':
        tag = 'error' if status == 'BLOCKED_INFRASTRUCTURE' else 'failure'
        ET.SubElement(case, tag, message=status)
    ET.SubElement(case, 'system-out').text = out
    ET.SubElement(case, 'system-err').text = err

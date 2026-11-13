"""Comparar la misma carga binaria contra F+E y P0.2-G."""
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

from verificar_errores import InvalidConfig, read_cache, sha256


def run_stress(run, args, lock, revision, classify, aggregate):
    binary = (args.stress_build / 'p04_carga').resolve()
    candidate = args.core_build.resolve()
    base = args.comparison_core_build.resolve()
    base_source = Path(read_cache(base)['CMAKE_HOME_DIRECTORY'])
    rc, sha, _ = run('stress-base-sha', ['git', '-C', base_source, 'rev-parse', 'HEAD'])
    if rc or sha.strip() != lock['core_revisions'][revision['stress']['base']]['sha']:
        raise InvalidConfig('Core base de la carga no coincide con el contrato')
    rc, dirty, _ = run('stress-base-status', ['git', '-C', base_source, 'status', '--porcelain'])
    if rc or dirty.strip():
        raise InvalidConfig('La base de la carga debe estar limpia')
    paths = {p: sha256(p) for p in [binary, base / 'liblatino.so', candidate / 'liblatino.so']}
    modes = [('fe', base, 'base'), ('g-sin', candidate, 'base'),
             ('g', candidate, 'recolectar')]
    for name, library, _ in modes:
        rc, out, err = run('stress-loader-' + name, ['ldd', '-r', binary], library=library)
        match = re.search(r'liblatino\.so => (.*?) \(', out)
        if rc or 'undefined symbol:' in out + err or not match or Path(match[1]).resolve() != library / 'liblatino.so':
            raise InvalidConfig('Biblioteca incorrecta en carga P0.4: ' + name)
    if args.profile == 'sanitizers':
        for name, path in [('harness', binary), ('baseline', base / 'liblatino.so')]:
            rc, out, _ = run('stress-instrumentation-' + name, ['nm', '-D', path])
            if rc or not all(mark in out for mark in ('__asan_', '__ubsan_')):
                raise InvalidConfig('Carga sin instrumentacion: ' + name)
    rows = []
    suite = ET.Element('testsuite', name='p04-carga')
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
            case = ET.SubElement(suite, 'testcase', name=label)
            if status != 'PASS':
                tag = 'error' if status == 'BLOCKED_INFRASTRUCTURE' else 'failure'
                ET.SubElement(case, tag, message=status)
            ET.SubElement(case, 'system-out').text = out
            ET.SubElement(case, 'system-err').text = err
    if any(sha256(p) != digest for p, digest in paths.items()):
        raise InvalidConfig('Cambio un binario durante la carga')
    ET.ElementTree(suite).write(args.output / 'stress.xml', encoding='utf-8', xml_declaration=True)
    return {'status': aggregate([r['status'] for r in rows])[0], 'cases': rows,
            'base_sha': sha.strip(), 'hashes': {str(p): h for p, h in paths.items()}}

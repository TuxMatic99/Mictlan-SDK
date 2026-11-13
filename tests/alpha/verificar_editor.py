"""Ejecuta los instaladores sobre rutas nuevas y comprueba el proyecto extraído."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

root, out = (Path(value).resolve() for value in sys.argv[1:])
out.mkdir()
extension = root / 'herramientas/vscode-mictlan'
env = dict(os.environ, XDG_DATA_HOME=str(out / 'xdg'),
           MICTLAN_VSCODE_EXTENSIONS_DIR=str(out / 'extensions'))


def run(*args, cwd=out):
    return subprocess.run(args, env=env, cwd=cwd, check=True, text=True,
                          stdout=subprocess.PIPE, timeout=25).stdout


manifest = json.loads((extension / 'package.json').read_text())
language, = manifest['contributes']['languages']
assert language['id'] == 'mictlan' and language['extensions'] == ['.mict']
name = run('python3', extension / 'identificador.py', extension / 'package.json').strip()
print(run('bash', extension / 'instalar-vscode.sh'), end='')
installed = out / 'extensions' / name
for f in ('package.json', language['configuration'], *language['icon'].values(),
          manifest['contributes']['grammars'][0]['path']):
    assert (extension / f).read_bytes() == (installed / f).read_bytes()
print(run('bash', extension / 'linux/instalar-mime.sh'), end='')
program = root / 'proyecto/primero.mict'
assert run('xdg-mime', 'query', 'filetype', program).strip() == 'text/x-mictlan'
assert run('xdg-mime', 'query', 'filetype',
           root / 'share/mictlan/ejemplos/hola_mictlan.lat').strip() != 'text/x-mictlan'
for size in [16, 24, 32, 48, 64, 128, 256]:
    icon = out / f'xdg/icons/hicolor/{size}x{size}/mimetypes/text-x-mictlan.png'
    assert icon.read_bytes() == (extension / f'icons/mictlan-light-{size}.png').read_bytes()

project = root / 'proyecto'
task, = json.loads((project / '.vscode/tasks.json').read_text())['tasks']
assert task['type'] == 'process'
variables = {'workspaceFolder': str(project), 'file': str(program), 'fileDirname': str(project)}


def resolve(value):
    for key, replacement in variables.items():
        value = value.replace('${' + key + '}', replacement)
    return value


result = run(resolve(task['command']), *map(resolve, task['args']), cwd=resolve(task['options']['cwd']))
assert result.splitlines()[-1] == 'El resultado es: 42'
print(run('bash', extension / 'desinstalar-vscode.sh'), end='')
assert not installed.exists()
print(json.dumps({'status': 'PASS', 'mime': 'text/x-mictlan', 'extension': name,
                  'tarea': task['label'], 'programa_sha256': hashlib.sha256(program.read_bytes()).hexdigest()}))

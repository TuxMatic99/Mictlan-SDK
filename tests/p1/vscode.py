#!/usr/bin/env python3
"""Comprueba tareas y diagnósticos de VS Code usando el paquete extraído."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess

p = argparse.ArgumentParser()
p.add_argument("prefijo", type=Path)
p.add_argument("salida", type=Path)
a = p.parse_args()
root, out = a.prefijo.resolve(), a.salida.resolve()
out.mkdir()
proyecto = root / "VectorLab"
editor = root / "herramientas/vscode-mictlan"
env = dict(os.environ, XDG_DATA_HOME=str(out / "xdg"),
           MICTLAN_VSCODE_EXTENSIONS_DIR=str(out / "extensiones"))
env.pop("LD_PRELOAD", None)
env.pop("LD_LIBRARY_PATH", None)


def run(*args, cwd=None):
    r = subprocess.run(args, env=env, cwd=cwd or out, check=True,
                       capture_output=True, text=True, timeout=20)
    return r.stdout


manifest = json.loads((editor / "package.json").read_text())
name = run("python3", editor / "identificador.py", editor / "package.json").strip()
installed = out / "extensiones" / name
run("bash", editor / "instalar-vscode.sh")
for f in sorted((editor / "icons").glob("*.png")):
    assert (installed / "icons" / f.name).read_bytes() == f.read_bytes(), f
run("bash", editor / "linux/instalar-mime.sh")
mime = run("gio", "info", "-a", "standard::content-type", proyecto / "principal.mict")
assert "standard::content-type: text/x-mictlan" in mime

matcher, = manifest["contributes"]["problemMatchers"]
pattern = matcher["pattern"]
assert [pattern[k] for k in ("file", "line", "column", "message")] == [1, 2, 3, 4]
tareas = json.loads((proyecto / ".vscode/tasks.json").read_text())["tasks"]
assert len(tareas) == 3 and all(t["problemMatcher"] == "$mictlan" and t["type"] == "process"
                               for t in tareas)
muestra = out / "diagnóstico.mict"
muestra.write_text('escribir(sin_definir)\n')


def argumentos(task, archivo):
    def expand(s):
        return s.replace("${workspaceFolder}", str(proyecto)).replace("${file}", str(archivo))
    return [expand(task["command"]), *map(expand, task["args"])], expand(task["options"]["cwd"])


consola, cwd = argumentos(tareas[0], muestra)
r = subprocess.run(consola, cwd=cwd, env=env, text=True, capture_output=True, timeout=15)
assert r.returncode == 1
match = re.match(pattern["regexp"], r.stderr)
assert match and match[1] == str(muestra) and match[2] == "1" and int(match[3]) > 0, r.stderr
grafica, _ = argumentos(tareas[1], muestra)
assert Path(grafica[0]).resolve() == root / "bin/mictlan-ui"
assert Path(grafica[-1]).resolve() == proyecto / "principal.mict"
assert run(grafica[0], "--version").startswith("Mictlán UI ")
pruebas, cwd = argumentos(tareas[2], muestra)
assert "sesión comprobada" in run(*pruebas, cwd=cwd)
run("bash", editor / "desinstalar-vscode.sh")
assert not installed.exists()
(out / "vscode.json").write_text(json.dumps({"status": "PASS", "tareas": 3,
    "linea": int(match[2]), "columna": int(match[3]), "iconos": "idénticos",
    "alcance": "Comandos, manifest, MIME y diagnóstico. Revisión gráfica manual."}, ensure_ascii=False) + "\n")

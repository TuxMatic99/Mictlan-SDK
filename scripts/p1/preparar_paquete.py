#!/usr/bin/env python3
"""Crea y verifica el ZIP de aplicaciones en un prefijo nuevo."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import stat
import subprocess
import zipfile

SDK = Path(__file__).resolve().parents[2]
p = argparse.ArgumentParser(description=__doc__)
for name in ["core", "core-build", "sdk-build", "lab", "raylib", "raylib-lib", "output"]:
    p.add_argument("--" + name, type=Path, required=True)
a = p.parse_args()
for name, value in vars(a).items():
    setattr(a, name, value.resolve())
lock = json.loads((SDK / "ci/p1/revisiones.json").read_text())
env = dict(os.environ, LC_ALL="C.UTF-8")
for key in ("LD_LIBRARY_PATH", "LD_PRELOAD", "PYTHONPATH"):
    env.pop(key, None)


def run(*args, cwd=None, quiet=True):
    return subprocess.run(args, cwd=cwd, env=env, text=True, check=True,
                          stdout=subprocess.PIPE if quiet else None, timeout=45).stdout


def exact(repo, expected=None):
    sha = run("git", "-C", repo, "rev-parse", "HEAD").strip()
    if expected and sha != expected:
        raise SystemExit(f"Revisión inesperada de {repo}: {sha}")
    if run("git", "-C", repo, "status", "--porcelain"):
        raise SystemExit(f"Se requiere un árbol limpio: {repo}")
    return sha


def release_cache(build, source):
    lines = (build / "CMakeCache.txt").read_text().splitlines()
    if (f"CMAKE_HOME_DIRECTORY:INTERNAL={source}" not in lines or
            "CMAKE_BUILD_TYPE:STRING=Release" not in lines or
            any("-fsanitize=" in line for line in lines if line.startswith("CMAKE_"))):
        raise SystemExit(f"Se requiere la compilación Release exacta: {build}")
    return lines


def copy(source, target, mode=0o644):
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    target.chmod(mode)


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def dependencies(binary):
    return run("readelf", "-d", binary)


if platform.system() != "Linux" or platform.machine() != "x86_64":
    raise SystemExit("La distribución requiere Linux x86_64")
core_sha = exact(a.core, lock["core"])
lab_sha = exact(a.lab, lock["lab"])
raylib_sha = exact(a.raylib, lock["raylib"])
sdk_sha = exact(SDK)
release_cache(a.core_build, a.core)
cache = release_cache(a.sdk_build, SDK)
library = a.core_build / "liblatino.so"
if not any(line.startswith("LATINO_LIBRARY:") and line.endswith("=" + str(library)) for line in cache):
    raise SystemExit("La biblioteca de la compilación SDK debe ser la del Core fijado")
resolved = run("ldd", "-r", a.sdk_build / "host_ui")
for name, path in (("liblatino.so", library), ("libraylib.so.550", a.raylib_lib)):
    m = re.search(r"^\s*" + re.escape(name) + r" => (.*?) \(", resolved, re.M)
    if not m or Path(m[1]).resolve() != path.resolve():
        raise SystemExit(f"Biblioteca de compilación no comprobada: {name}")

version = run(a.core_build / "mictlan", "--version").strip().removeprefix("Mictlán ")
if not re.fullmatch(r"\d+\.\d+\.\d+-alpha", version):
    raise SystemExit("Versión de producto inesperada")
a.output.mkdir()
name = f"mictlan-aplicaciones-{version}-linux-x86_64"
root = a.output / name
root.mkdir()
run("cmake", "--install", a.core_build, "--prefix", root, "--component", "MictlanPortable", quiet=False)
run("cmake", "--install", a.sdk_build, "--prefix", root, "--component", "MictlanAplicaciones", quiet=False)
(root / "bin/host_ui").rename(root / "bin/mictlan-ui")
(root / "bin/mictlan_ciencia_consola").rename(root / "bin/mictlan-ciencia")
copy(library, root / "lib/liblatino.so")
copy(a.raylib_lib, root / "lib/libraylib.so.550")
copy(a.raylib / "LICENSE", root / "share/doc/mictlan/LICENSE-Raylib")
copy(SDK / "LICENSE", root / "share/doc/mictlan/LICENSE-SDK")
copy(SDK / "herramientas/vscode-mictlan/icons/mictlan-light-256.png",
     root / "share/mictlan/recursos/Mictlan.png")
shutil.copytree(SDK / "herramientas/vscode-mictlan", root / "herramientas/vscode-mictlan")
shutil.copytree(a.lab / "VectorLab", root / "VectorLab")
copy(SDK / "ejemplos/p1/vscode-tasks.json", root / "VectorLab/.vscode/tasks.json")
copy(SDK / "ejemplos/p1/contador.mict", root / "share/mictlan/ejemplos/contador.mict")
copy(SDK / "scripts/p1/probar-vectorlab", root / "bin/probar-vectorlab", 0o755)
copy(SDK / "docs/p1/DISTRIBUCION.md", root / "README.md")
for doc in ("API.md", "ARQUITECTURA.md"):
    copy(SDK / "docs/p1" / doc, root / "share/doc/mictlan" / doc)

versions = {"core": core_sha, "sdk": sdk_sha, "lab": lab_sha, "raylib": raylib_sha,
            "raylib_so_sha256": digest(a.raylib_lib), "version": version,
            "sistema": Path("/etc/os-release").read_text(),
            "compilador": run("cc", "--version").splitlines()[0],
            "cmake": run("cmake", "--version").splitlines()[0]}
(root / "VERSIONES.json").write_text(json.dumps(versions, indent=2, ensure_ascii=False) + "\n")
paths = sorted(path for path in root.rglob("*") if path.is_file())
manifest = "".join(f"{digest(path)}  {path.relative_to(root).as_posix()}\n" for path in paths)
(root / "SHA256SUMS").write_text(manifest)
archive = a.output / (name + ".zip")
with zipfile.ZipFile(archive, "x", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        entry = zipfile.ZipInfo(path.relative_to(root.parent).as_posix(), (1980, 1, 1, 0, 0, 0))
        entry.create_system = 3
        entry.external_attr = (stat.S_IFREG | stat.S_IMODE(path.stat().st_mode)) << 16
        z.writestr(entry, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
(a.output / (archive.name + ".sha256")).write_text(f"{digest(archive)}  {archive.name}\n")

extraido = a.output / "extraído limpio"
extraido.mkdir()
run("unzip", "-q", archive, "-d", extraido)
prefijo = extraido / name
run("sha256sum", "-c", "SHA256SUMS", cwd=prefijo, quiet=False)
for executable, expected in (("mictlan", f"Mictlán {version}"),
                             ("mictlan-ui", f"Mictlán UI {version}")):
    if run(prefijo / "bin" / executable, "--version", cwd=extraido).strip() != expected:
        raise SystemExit(f"Identidad incorrecta de {executable}")
loader = {}
for executable in ("mictlan", "mictlan-ui", "mictlan-ciencia"):
    binary = prefijo / "bin" / executable
    dep = run("ldd", "-r", binary, cwd=extraido)
    if "not found" in dep or "undefined symbol:" in dep:
        raise SystemExit(dep)
    for shared in ("liblatino.so", "libraylib.so.550"):
        match = re.search(r"^\s*" + re.escape(shared) + r" => (.*?) \(", dep, re.M)
        expected = executable == "mictlan-ui" or (shared == "liblatino.so" and executable == "mictlan-ciencia")
        if expected and (not match or Path(match[1]).resolve() != prefijo / "lib" / shared):
            raise SystemExit(f"Resolución externa inesperada: {executable} / {shared}")
        if not expected and match:
            raise SystemExit(f"Dependencia gráfica en {executable}: {shared}")
    if executable == "mictlan" and re.search(r"libraylib|libGL|libX11", dependencies(binary) + dep):
        raise SystemExit("Dependencia gráfica en la consola")
    loader[executable] = dep
for suffix in ("lat", "mict"):
    hello = prefijo / f"share/mictlan/ejemplos/hola_mictlan.{suffix}"
    if run(prefijo / "bin/mictlan", hello, cwd=extraido).splitlines()[-1:] != ["El resultado es: 42"]:
        raise SystemExit(f"Ejemplo de consola incorrecto: {suffix}")
run(prefijo / "bin/probar-vectorlab", cwd=extraido, quiet=False)
result = {"status": "PASS", "versions": versions, "zip": archive.name, "sha256": digest(archive),
          "extraido": str(prefijo), "cargador": loader}
(a.output / "paquete.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
print(prefijo)

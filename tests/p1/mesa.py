#!/usr/bin/env python3
"""Vincula las trazas estrictas con los binarios mapeados antes del cierre."""
import argparse
from bisect import bisect_right
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

p = argparse.ArgumentParser(description=__doc__)
p.add_argument("salidas", type=Path)
p.add_argument("reporte", type=Path)
p.add_argument("--biblioteca", type=Path, help="Binario Gallium de la versión exacta del runner")
p.add_argument("--simbolos", type=Path, help="ELF de símbolos con el mismo Build ID")
a = p.parse_args()
a.reporte.mkdir()
env = dict(os.environ, DEBUGINFOD_URLS=os.environ.get("DEBUGINFOD_URLS", ""),
           DEBUGINFOD_TIMEOUT="10", DEBUGINFOD_MAXSIZE="150000000", DEBUGINFOD_RETRY_LIMIT="0")
modulos = {}
tablas = {}


def ejecutar(*args, timeout=15):
    try:
        r = subprocess.run(args, env=env, text=True, capture_output=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return 1, str(exc)
    return r.returncode, r.stdout.strip() if r.returncode == 0 else r.stderr.strip()


def modulo(ruta):
    if ruta not in modulos:
        binario = a.biblioteca if a.biblioteca and a.biblioteca.name == Path(ruta).name else ruta
        rc, elf = ejecutar("readelf", "-n", binario)
        match = re.search(r"Build ID: (\w+)", elf)
        build_id = match[1] if rc == 0 and match else None
        archivo = (a.simbolos if a.simbolos else
                   "/usr/lib/debug/.build-id/" + build_id[:2] + "/" + build_id[2:] + ".debug") if build_id else None
        razon = None
        if archivo and not Path(archivo).is_file():
            archivo = None
            if shutil.which("debuginfod-find") and env["DEBUGINFOD_URLS"]:
                estado, valor = ejecutar("debuginfod-find", "debuginfo", build_id, timeout=35)
                if estado == 0 and Path(valor).is_file():
                    archivo = valor
                else:
                    razon = valor
        if archivo:
            rc, salida = ejecutar("readelf", "-n", archivo)
            if rc or f"Build ID: {build_id}" not in salida:
                archivo, razon = None, "Build ID de símbolos no coincide"
        if archivo:
            rc, salida = ejecutar("nm", "-n", "-S", "--defined-only", archivo)
            if rc == 0:
                filas = []
                for linea in salida.splitlines():
                    partes = linea.split(maxsplit=3)
                    if len(partes) == 4 and partes[2] in {"t", "T", "w", "W"}:
                        inicio = int(partes[0], 16)
                        filas.append((inicio, inicio + int(partes[1], 16), partes[3]))
                tablas[ruta] = ([f[0] for f in filas], filas)
            else:
                razon = salida
        modulos[ruta] = {"build_id": build_id, "debug": str(archivo) if archivo else None,
                         "busqueda": razon}
    return modulos[ruta]


def simbolo(ruta, offset):
    if ruta not in tablas:
        return None
    inicios, filas = tablas[ruta]
    direccion = int(offset, 16)
    i = bisect_right(inicios, direccion) - 1
    if i >= 0:
        inicio, fin, nombre = filas[i]
        if inicio <= direccion < fin:
            return f"{nombre}+{hex(direccion - inicio)}"
    return None


casos = []
for maps in sorted(a.salidas.glob("ventana*/casos/*/maps.log")):
    stderr = maps.with_name("stderr.log")
    if not stderr.is_file():
        continue
    rangos = []
    for linea in maps.read_text().splitlines():
        m = re.match(r"([0-9a-f]+)-([0-9a-f]+) \S+ ([0-9a-f]+) \S+ \d+\s+(/.+)", linea)
        if m:
            rangos.append((*map(lambda s: int(s, 16), m.groups()[:3]), m[4]))
    texto = stderr.read_text(errors="replace")
    bloques = re.split(r"(?=(?:Direct|Indirect) leak of \d+ byte)", texto)
    fugas = []
    for bloque in bloques:
        m = re.match(r"(Direct|Indirect) leak of (\d+) byte", bloque)
        if not m:
            continue
        frames = []
        for frame in re.finditer(r"^\s*#(\d+) 0x([0-9a-f]+) (.*)$", bloque, re.M):
            nivel = int(frame[1])
            direccion = int(frame[2], 16)
            if nivel == 0:
                continue  # asignador de ASan
            for inicio, fin, desplazamiento, ruta in rangos:
                if inicio <= direccion < fin:
                    offset = hex(direccion - inicio + desplazamiento)
                    registro = {"nivel": nivel, "modulo": ruta, "offset_elf": offset, "original": frame[3]}
                    if "libgallium" in ruta:
                        info = modulo(ruta)
                        registro["build_id"] = info["build_id"]
                        registro["simbolo"] = simbolo(ruta, offset)
                    frames.append(registro)
                    break
        fugas.append({"clase": m[1], "bytes": int(m[2]), "traza": frames})
    casos.append({"caso": str(maps.parent.relative_to(a.salidas)), "fugas": fugas})

reporte = {"casos": casos, "modulos": modulos, "estricto": True,
           "alcance": "Esta simbolización no cambia el estado de las pruebas de ventana."}
(a.reporte / "mesa.json").write_text(json.dumps(reporte, ensure_ascii=False, indent=2) + "\n")

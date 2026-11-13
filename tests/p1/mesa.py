#!/usr/bin/env python3
"""Vincula las trazas estrictas con los binarios mapeados antes del cierre."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

p = argparse.ArgumentParser(description=__doc__)
p.add_argument("salidas", type=Path)
p.add_argument("reporte", type=Path)
a = p.parse_args()
a.reporte.mkdir()
env = dict(os.environ, DEBUGINFOD_URLS=os.environ.get("DEBUGINFOD_URLS", ""),
           DEBUGINFOD_TIMEOUT="10", DEBUGINFOD_MAXSIZE="150000000", DEBUGINFOD_RETRY_LIMIT="0")
modulos = {}


def ejecutar(*args, timeout=15):
    try:
        r = subprocess.run(args, env=env, text=True, capture_output=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return 1, str(exc)
    return r.returncode, r.stdout.strip() if r.returncode == 0 else r.stderr.strip()


def modulo(ruta):
    if ruta not in modulos:
        rc, elf = ejecutar("readelf", "-n", ruta)
        match = re.search(r"Build ID: (\w+)", elf)
        build_id = match[1] if rc == 0 and match else None
        archivo = "/usr/lib/debug/.build-id/" + build_id[:2] + "/" + build_id[2:] + ".debug" if build_id else None
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
        modulos[ruta] = {"build_id": build_id, "debug": archivo, "busqueda": razon}
    return modulos[ruta]


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
                        if info["debug"]:
                            rc, simbolo = ejecutar("addr2line", "-f", "-C", "-i", "-e", info["debug"], offset)
                            if rc == 0:
                                registro["simbolo"] = simbolo
                    frames.append(registro)
                    break
        fugas.append({"clase": m[1], "bytes": int(m[2]), "traza": frames})
    casos.append({"caso": str(maps.parent.relative_to(a.salidas)), "fugas": fugas})

reporte = {"casos": casos, "modulos": modulos, "estricto": True,
           "alcance": "Esta simbolización no cambia el estado de las pruebas de ventana."}
(a.reporte / "mesa.json").write_text(json.dumps(reporte, ensure_ascii=False, indent=2) + "\n")

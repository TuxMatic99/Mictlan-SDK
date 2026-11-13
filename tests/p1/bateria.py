#!/usr/bin/env python3
"""Compara cargas fijas del mismo backend de prueba y verifica el inventario."""
import argparse
import json
import os
from pathlib import Path
import re
import statistics
import subprocess
import xml.etree.ElementTree as ET

p = argparse.ArgumentParser(description=__doc__)
p.add_argument("build", type=Path)
p.add_argument("lab", type=Path)
p.add_argument("salida", type=Path)
p.add_argument("--perfil", choices=["debug", "release", "sanitizers"], default="release")
p.add_argument("--anterior", type=Path)
a = p.parse_args()
root = Path(__file__).resolve().parents[2]
lab, build, out = a.lab.resolve(), a.build.resolve(), a.salida.resolve()
out.mkdir()
env = dict(os.environ, LC_ALL="C.UTF-8", MICTLAN_UI_METRICAS="1")
if a.perfil == "sanitizers":
    env.update(ASAN_OPTIONS="detect_leaks=1:halt_on_error=1:exitcode=86",
               UBSAN_OPTIONS="halt_on_error=1:print_stacktrace=1:exitcode=86",
               LSAN_OPTIONS="leak_check_at_exit=1:exitcode=86")
status = "FAIL_PROGRAM"
rows = {}
suite = ET.Element("testsuite", name="p1-aplicaciones")
harness = build / "test_ui_host"
aplicacion = lab / "VectorLab"


def ejecutar(nombre, argv, cwd=out, extra=None):
    global status
    caso = ET.SubElement(suite, "testcase", name=nombre)
    entorno = dict(env, **(extra or {}))
    r = subprocess.run(argv, env=entorno, cwd=cwd, text=True, capture_output=True, timeout=65)
    (out / f"{nombre}.stdout.log").write_text(r.stdout)
    (out / f"{nombre}.stderr.log").write_text(r.stderr)
    ET.SubElement(caso, "system-out").text = r.stdout
    ET.SubElement(caso, "system-err").text = r.stderr
    memoria = re.search(r"ERROR: (AddressSanitizer|LeakSanitizer)|UndefinedBehaviorSanitizer|runtime error:", r.stderr)
    informe = re.search(r"AddressSanitizer|LeakSanitizer|UndefinedBehaviorSanitizer|runtime error:", r.stderr + r.stdout)
    if memoria:
        status = "FAIL_SANITIZER"
    elif "does not work under ptrace" in r.stderr:
        status = "BLOCKED_INFRASTRUCTURE"
    elif informe:
        status = "FAIL_SANITIZER"
    elif r.returncode:
        status = "FAIL_PROGRAM"
    if r.returncode or informe:
        ET.SubElement(caso, "failure", message=status)
        raise RuntimeError(f"{nombre}: {status} ({r.returncode})\n{r.stderr[-4000:]}")
    return r.stdout


def carga(nombre, archivo, cantidad):
    stdout = ejecutar(nombre, [harness, "--p1-carga", archivo],
                      extra={"MICTLAN_UI_CARGA": str(cantidad)})
    datos = json.loads(next(s.split(" ", 1)[1] for s in stdout.splitlines()
                            if s.startswith("MICTLAN_UI_METRICAS ")))
    assert datos["cuadros"] == datos["eventos_entregados"] == cantidad, datos
    rows[nombre] = datos


try:
    for caso, mensaje in [("operaciones", "cálculos y validación correctos"), ("sesion", "sesión comprobada")]:
        carpeta = out / caso
        carpeta.mkdir()
        stdout = ejecutar(caso, [build / "mictlan_ciencia_consola",
                          aplicacion / f"pruebas/{caso}.mict"], cwd=carpeta)
        assert mensaje in stdout, stdout
    ejecutar("vectorlab-dibujo", ["python3", root / "tests/p1/ejecutar_host.py", harness,
                                 "vectorlab", aplicacion / "principal.mict"])
    carga("vectorlab-100", aplicacion / "principal.mict", 100)
    carga("vectorlab-1000", aplicacion / "principal.mict", 1000)
    inicio, final = rows["vectorlab-100"], rows["vectorlab-1000"]
    assert final["lineas"] >= 22 and final["bytes_vm"] <= inicio["bytes_vm"] + 1024 * 1024, rows
    if a.anterior:
        anterior = a.anterior.resolve()
        for i in range(3):
            carga(f"p1-{i}", root / "tests/p1/carga.mict", 1000)
            stdout = ejecutar(f"anterior-{i}", [anterior, "--p1-carga", root / "tests/p1/carga.mict"],
                              extra={"MICTLAN_UI_CARGA": "1000"})
            datos = json.loads(next(s.split(" ", 1)[1] for s in stdout.splitlines()
                                    if s.startswith("MICTLAN_UI_METRICAS ")))
            assert datos["cuadros"] == datos["eventos_entregados"] == 1000, datos
            rows[f"anterior-{i}"] = datos
        rows["comparacion_mediana_ms"] = {
            nombre: statistics.median(rows[f"{nombre}-{i}"]["ms"] for i in range(3))
            for nombre in ("p1", "anterior")}
    status = "PASS"
except Exception as e:
    ET.SubElement(ET.SubElement(suite, "testcase", name="aceptación"), "failure",
                  message=str(e))
    raise
finally:
    ET.ElementTree(suite).write(out / "aplicaciones.xml", encoding="utf-8", xml_declaration=True)
    (out / "aplicaciones.json").write_text(json.dumps({"status": status, "perfil": a.perfil,
        "cargas": rows}, ensure_ascii=False, indent=2) + "\n")

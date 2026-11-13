#!/usr/bin/env python3
"""Mide la misma carga con Core Alpha, P1.1 y el recolector experimental."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET

SDK = Path(__file__).resolve().parents[2]
p = argparse.ArgumentParser(description=__doc__)
p.add_argument("host", type=Path)
p.add_argument("lab", type=Path)
p.add_argument("salida", type=Path)
p.add_argument("--base", type=Path)
p.add_argument("--larga", action="store_true")
p.add_argument("--sanitizers", action="store_true")
a = p.parse_args()
a.host, a.lab, a.salida = (path.resolve() for path in (a.host, a.lab, a.salida))
if a.base:
    a.base = a.base.resolve()
a.salida.mkdir()
resultados = {}
suite = ET.Element("testsuite", name="p11-aplicaciones-memoria")
env = dict(os.environ, LC_ALL="C.UTF-8", MICTLAN_UI_METRICAS="1")
env.pop("MICTLAN_UI_PRUEBA_GC", None)
if a.sanitizers:
    env.update(ASAN_OPTIONS="detect_leaks=1:halt_on_error=1:exitcode=86",
               UBSAN_OPTIONS="halt_on_error=1:print_stacktrace=1:exitcode=86",
               LSAN_OPTIONS="leak_check_at_exit=1:exitcode=86")


class Fallo(Exception):
    def __init__(self, estado, mensaje):
        super().__init__(mensaje)
        self.estado = estado


def comprobar(condicion, mensaje):
    if not condicion:
        raise Fallo("FAIL_PROGRAM", mensaje)


def ejecutar(nombre, binario, opcion, script, modo=None, cantidad=1000, gc=False):
    caso = ET.SubElement(suite, "testcase", name=nombre)
    dir_trabajo = a.salida / nombre
    dir_trabajo.mkdir()
    if modo:
        (dir_trabajo / "modo-p11.txt").write_text(modo)
    opciones = dict(env, MICTLAN_UI_CARGA=str(cantidad))
    if gc:
        opciones["MICTLAN_UI_PRUEBA_GC"] = "1"
    comando = [str(binario), opcion, str(script)]
    try:
        proceso = subprocess.run(comando, cwd=dir_trabajo, env=opciones, text=True,
                                 capture_output=True, timeout=300)
    except subprocess.TimeoutExpired as exc:
        (dir_trabajo / "stdout.log").write_bytes(exc.stdout or b"")
        (dir_trabajo / "stderr.log").write_bytes(exc.stderr or b"")
        raise Fallo("FAIL_TIMEOUT", nombre) from exc
    (dir_trabajo / "stdout.log").write_text(proceso.stdout)
    (dir_trabajo / "stderr.log").write_text(proceso.stderr)
    ET.SubElement(caso, "system-out").text = proceso.stdout
    ET.SubElement(caso, "system-err").text = proceso.stderr
    todo = proceso.stdout + proceso.stderr
    if re.search(r"ERROR: (AddressSanitizer|LeakSanitizer)|UndefinedBehaviorSanitizer|runtime error:", todo):
        raise Fallo("FAIL_SANITIZER", f"{nombre}: {todo[-2000:]}")
    if "LeakSanitizer does not work under ptrace" in todo:
        raise Fallo("BLOCKED_INFRASTRUCTURE", nombre)
    if re.search(r"AddressSanitizer|LeakSanitizer", todo):
        raise Fallo("FAIL_SANITIZER", f"{nombre}: {todo[-2000:]}")
    comprobar(proceso.returncode == 0, f"{nombre}: {proceso.returncode} {todo[-2000:]}")
    linea = next((l.split(" ", 1)[1] for l in proceso.stdout.splitlines()
                  if l.startswith("MICTLAN_UI_METRICAS ")), None)
    comprobar(linea is not None, f"{nombre}: no hay métricas")
    datos = json.loads(linea)
    datos.update(comando=comando, gc_solicitado=gc)
    resultados[nombre] = datos
    if opcion == "--p1-carga":
        comprobar(datos["cuadros"] == datos["eventos_entregados"] == cantidad, nombre)
    if modo == "sesion":
        comprobar((dir_trabajo / "salida-p11.txt").read_text() == f"Entrada {cantidad}", nombre)
    return datos, todo, dir_trabajo


def informar():
    carga = SDK / "tests/p1/carga_memoria.mict"
    muestras = [1000, 10000, 100000] if a.larga else [1000, 10000]
    if a.sanitizers:
        muestras = [1000]
    for modo in ("repetida", "variable", "invalida", "sesion"):
        for cantidad in muestras:
            if a.base:
                ejecutar(f"base-{modo}-{cantidad}", a.base, "--p1-carga", carga, modo, cantidad)
            datos, _, _ = ejecutar(f"gc-{modo}-{cantidad}", a.host, "--p1-carga",
                                   carga, modo, cantidad, gc=True)
            comprobar(datos["gc_estado"] == 0 and datos["gc_reservas"] > 0, modo)
        if len(muestras) > 1:
            primero = resultados[f"gc-{modo}-{muestras[0]}"]
            ultimo = resultados[f"gc-{modo}-{muestras[-1]}"]
            comprobar(ultimo["bytes_vm"] <= primero["bytes_vm"] + 1024 * 1024 and
                      ultimo["cadenas"] <= primero["cadenas"] + 16,
                      f"creció el conjunto final: {modo}")
    ejecutar("p11-sin-gc", a.host, "--p1-carga", carga, "variable", 1000)
    ejecutar("vectorlab-gc", a.host, "--p1-vectorlab",
             a.lab / "VectorLab/principal.mict", gc=True)
    registro, _, trabajo = ejecutar("registro-gc", a.host, "--p11-registro",
                                    a.lab / "Registro/principal.mict", gc=True)
    comprobar(registro["gc_estado"] == 0 and
              (trabajo / "registro-v1.txt").read_bytes() ==
              "Registro-v1\nMaría Ñáñez\nMedición \n".encode(), "Registro persistente")
    recuperado, stderr, _ = ejecutar("error-recuperado-gc", a.host, "--p1-error",
                                     SDK / "tests/p1/error_callback.mict", gc=True)
    comprobar("la VM recuperó su estado" in stderr and "se omite destructor" not in stderr
              and recuperado["gc_estado"] == 0, "cierre después de error")
    opaca, _, _ = ejecutar("nativa-opaca", a.host, "--p1-carga", SDK / "tests/p1/carga_opaca.mict",
                           cantidad=129, gc=True)
    comprobar(opaca["gc_estado"] == 3 and opaca["gc_recolecciones"] == 1, "caída segura a F")


estado = "PASS"
try:
    informar()
except (Fallo, OSError, ValueError) as exc:
    estado = exc.estado if isinstance(exc, Fallo) else "FAIL_CONFIGURATION"
    ET.SubElement(ET.SubElement(suite, "testcase", name="resultado"), "failure", message=str(exc))
    print(f"{estado} {exc}", file=sys.stderr)
finally:
    (a.salida / "memoria.json").write_text(json.dumps(
        {"status": estado, "casos": resultados}, ensure_ascii=False, indent=2) + "\n")
    ET.ElementTree(suite).write(a.salida / "memoria.xml", encoding="utf-8", xml_declaration=True)
sys.exit(estado != "PASS")

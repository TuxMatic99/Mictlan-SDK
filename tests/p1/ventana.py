#!/usr/bin/env python3
"""Comprueba ventanas de producción en un servidor X11 dedicado."""
import argparse
import contextlib
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import time

p = argparse.ArgumentParser(description=__doc__)
p.add_argument("paquete", type=Path)
p.add_argument("salida", type=Path)
p.add_argument("--host", type=Path)
p.add_argument("--anterior", type=Path)
p.add_argument("--perfil", choices=["release", "sanitizers"], default="release")
p.add_argument("--capturas", action="store_true")
a = p.parse_args()
root, out = a.paquete.resolve(), a.salida.resolve()
sdk = Path(__file__).resolve().parents[2]
host = a.host.resolve() if a.host else root / "bin/mictlan-ui"
out.mkdir()
env = dict(os.environ, LC_ALL="C.UTF-8", LIBGL_ALWAYS_SOFTWARE="1", MICTLAN_UI_METRICAS="1")
env.pop("LD_PRELOAD", None)
env.pop("LD_LIBRARY_PATH", None)
if a.perfil == "sanitizers":
    env.update(ASAN_OPTIONS="detect_leaks=1:halt_on_error=1:exitcode=86",
               UBSAN_OPTIONS="halt_on_error=1:print_stacktrace=1:exitcode=86",
               LSAN_OPTIONS="leak_check_at_exit=1:exitcode=86")
report = {"status": "FAIL_PROGRAM", "cases": {}, "entorno": "X11 virtual, Mesa software"}
bad = re.compile(r"AddressSanitizer|UndefinedBehaviorSanitizer|LeakSanitizer|runtime error:")

def revisar_sanitizadores(stdout, stderr):
    if bad.search(stdout + stderr):
        report["status"] = ("BLOCKED_INFRASTRUCTURE" if "does not work under ptrace" in stderr
                            and not re.search(r"ERROR: (AddressSanitizer|LeakSanitizer)|runtime error:", stderr)
                            else "FAIL_SANITIZER")
        raise RuntimeError(stderr)


def x(*args, timeout=12):
    return subprocess.run(args, env=env, check=True, capture_output=True, text=True,
                          timeout=timeout).stdout.strip()


def hasta(condicion, explicacion, segundos=6):
    fin = time.monotonic() + segundos
    while time.monotonic() < fin:
        valor = condicion()
        if valor:
            return valor
        time.sleep(0.06)
    raise RuntimeError(explicacion)


def ventana(proc, titulo):
    try:
        ids = x("xdotool", "search", "--sync", "--onlyvisible", "--pid", str(proc.pid),
                "--name", titulo).splitlines()
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError) as exc:
        raise RuntimeError(f"No se abrió la ventana {titulo}. Estado {proc.poll()}") from exc
    assert len(ids) == 1 and ids[0].isdigit(), ids
    wid = ids[0]
    activar(wid)
    time.sleep(0.26)
    return wid


def activar(wid):
    x("xdotool", "windowactivate", "--sync", wid)
    assert x("xdotool", "getactivewindow") == wid


def tecla(key):
    x("xdotool", "keydown", key)
    time.sleep(0.12)
    x("xdotool", "keyup", key)
    time.sleep(0.12)


def escribir(texto):
    for signo in texto:
        tecla(signo)


def pulsar(wid, xpix, ypix):
    x("xdotool", "mousemove", "--window", wid, str(xpix), str(ypix))
    x("xdotool", "mousedown", "1")
    time.sleep(0.12)
    x("xdotool", "mouseup", "1")
    time.sleep(0.14)


def cerrar(wid):
    x("wmctrl", "-i", "-c", hex(int(wid)))


def geometria(wid):
    vals = dict(s.split("=", 1) for s in x("xdotool", "getwindowgeometry", "--shell", wid).splitlines())
    return int(vals["WIDTH"]), int(vals["HEIGHT"])


def boton(wid, columna):
    ancho, alto = geometria(wid)
    columna_ancho = (ancho - 48 - 16) / 2
    cuadro_ancho = (columna_ancho - 24) / 4
    cuadro_alto = (alto - 110 - 8 * 8) / 9
    pulsar(wid, int(24 + (columna + 0.5) * cuadro_ancho + 8 * columna),
           int(70 + 3 * (cuadro_alto + 8) + cuadro_alto / 2))


@contextlib.contextmanager
def ejecutar(nombre, binario, archivo):
    trabajo = out / nombre
    trabajo.mkdir()
    stdout, stderr = trabajo / "stdout.log", trabajo / "stderr.log"
    with stdout.open("wb") as o, stderr.open("wb") as e:
        proc = subprocess.Popen([binario, archivo], cwd=trabajo, env=env, stdout=o, stderr=e)
        try:
            yield proc, trabajo
        finally:
            if proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait(timeout=3)


def resultado(proc, trabajo, esperado=0, diagnostico=None):
    rc = proc.wait(timeout=12)
    stdout = (trabajo / "stdout.log").read_text(errors="replace")
    stderr = (trabajo / "stderr.log").read_text(errors="replace")
    revisar_sanitizadores(stdout, stderr)
    assert rc == esperado, (rc, stderr, stdout[-3000:])
    assert "Window closed successfully" in stdout, stdout[-3000:]
    if diagnostico:
        assert diagnostico in stderr and "se omite destructor" not in stderr, stderr
    else:
        assert not stderr, stderr
    record = {"status": "PASS", "returncode": rc}
    rows = [s for s in stdout.splitlines() if s.startswith("MICTLAN_UI_METRICAS ")]
    if rows:
        m = json.loads(rows[-1].split(" ", 1)[1])
        if m["ms"] > 0:
            m["fps_observados"] = 1000 * m["cuadros"] / m["ms"]
        record["metricas"] = m
    return record


def captura(wid, destino):
    data = subprocess.check_output(["import", "-window", wid, "-depth", "8", "ppm:-"],
                                   env=env, timeout=15)
    # PPM P6 de ImageMagick. Las líneas normalizadas deben estar en los píxeles.
    m = re.match(rb"P6\s+(\d+)\s+(\d+)\s+255\n", data)
    assert m, data[:120]
    width, height = map(int, m.groups())
    pix = data[m.end():]
    assert len(pix) == width * height * 3, (width, height, len(pix))
    colors = {"azul": bytes((15, 90, 164)), "naranja": bytes((176, 64, 22)), "ejes": bytes((99, 115, 133))}
    count = dict.fromkeys(colors, 0)
    for y in range(70, height - 40):
        for x in range(width // 2, width):
            offset = 3 * (y * width + x)
            value = pix[offset:offset + 3]
            for color, rgb in colors.items():
                count[color] += value == rgb
    assert count["azul"] > 15 and count["naranja"] > 15 and count["ejes"] > 100, count
    subprocess.run(["convert", "ppm:-", str(destino)], env=env, check=True,
                   input=data, timeout=15)
    return {"ancho": width, "alto": height, "colores": count,
            "sha256": hashlib.sha256(destino.read_bytes()).hexdigest()}


def sesion(path):
    try:
        return path.read_text().splitlines()
    except FileNotFoundError:
        return None


def vectorlab():
    principal = root / "VectorLab/principal.mict"
    with ejecutar("vectorlab", host, principal) as (proc, dir):
        wid = ventana(proc, "^VectorLab Mictlán$")
        assert geometria(wid) == (1080, 720), geometria(wid)
        imagenes = [captura(wid, dir / "inicio.png")] if a.capturas else []
        tecla("BackSpace")
        escribir("0")
        tecla("Return")
        boton(wid, 1)
        datos = dir / "vectorlab-v1.txt"
        esperado = ["VectorLab-v1", "0", "4", "5", "12"]
        hasta(lambda: sesion(datos) == esperado, "Guardar no escribió los valores editados")

        # Un campo se activa con el ratón y conserva UTF-8 en el runtime.
        pulsar(wid, 199, 99)
        tecla("BackSpace")
        escribir("x")
        tecla("Return")
        boton(wid, 1)
        assert sesion(datos) == esperado, "Una entrada inválida reemplazó la sesión"
        boton(wid, 2)
        boton(wid, 1)
        assert sesion(datos) == esperado, "Cargar no restauró la sesión válida"

        x("xdotool", "windowsize", "--sync", wid, "1200", "760")
        hasta(lambda: geometria(wid) == (1200, 760), "No se aplicó el redimensionamiento")
        time.sleep(0.30)
        if a.capturas:
            imagenes.append(captura(wid, dir / "redimensionada.png"))
        cerrar(wid)
        r = resultado(proc, dir)
        m = r["metricas"]
        assert m["eventos_entregados"] >= 6 and m["lineas"] >= 22, m
        assert (m["ancho"], m["alto"]) == (1200, 760), m
        r["capturas"] = imagenes
        r["sesion"] = sesion(datos)
        return r


def general():
    programa = root / "share/mictlan/ejemplos/contador.mict"
    with ejecutar("contador", host, programa) as (proc, dir):
        wid = ventana(proc, "Mictlán UI · Contador")
        assert geometria(wid) == (760, 480)
        tecla("Return")
        tecla("Tab")
        tecla("Return")
        r = resultado(proc, dir)
        assert r["metricas"]["eventos_entregados"] == 2
        return r


def error_callback():
    with ejecutar("error-callback", host, sdk / "tests/p1/error_callback.mict") as (proc, dir):
        wid = ventana(proc, "Mictlán UI|LatinoUI")
        tecla("Return")
        return resultado(proc, dir, 1, "la VM recuperó su estado")


def rss(pid):
    status = Path(f"/proc/{pid}/status").read_text()
    return {k: int(re.search(rf"^{k}:\s+(\d+)", status, re.M)[1]) for k in ("VmRSS", "VmHWM")}


def carga(nombre, binario):
    with ejecutar(nombre, binario, sdk / "tests/p1/carga.mict") as (proc, dir):
        wid = ventana(proc, "Carga de callbacks")
        antes = rss(proc.pid)
        start = time.monotonic()
        for _ in range(60):
            tecla("Return")
        despues = rss(proc.pid)
        while time.monotonic() - start < 18:
            time.sleep(0.1)
        segundos = time.monotonic() - start
        cerrar(wid)
        r = resultado(proc, dir)
        output = (dir / "stdout.log").read_text()
        assert [int(s) for s in output.splitlines() if s.isdecimal()] == list(range(1, 61)), output[-2500:]
        r.update({"eventos": 60, "segundos": segundos, "rss_kib_antes": antes, "rss_kib_despues": despues})
        return r


try:
    requisitos = ["xdotool", "wmctrl"] + (["import", "convert"] if a.capturas else [])
    if not env.get("DISPLAY") or any(not shutil.which(cmd) for cmd in requisitos):
        report["status"] = "BLOCKED_INFRASTRUCTURE"
        raise RuntimeError("Falta servidor X11 o alguna herramienta de la prueba")
    try:
        report["gestor"] = x("wmctrl", "-m")
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        report["status"] = "BLOCKED_INFRASTRUCTURE"
        raise
    report["cases"]["contador"] = general()
    report["cases"]["vectorlab"] = vectorlab()
    report["cases"]["error_callback"] = error_callback()
    if a.anterior:
        report["cases"]["carga_anterior"] = carga("carga-anterior", a.anterior.resolve())
        report["cases"]["carga_p1"] = carga("carga-p1", host)
    report["status"] = "PASS"
finally:
    (out / "ventana.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")

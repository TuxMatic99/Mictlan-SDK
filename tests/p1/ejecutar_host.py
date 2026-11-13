#!/usr/bin/env python3
"""Acredita la salida del host de prueba y rechaza diagnósticos inesperados."""
import argparse
import json
import re
import subprocess
import sys

p = argparse.ArgumentParser()
p.add_argument("programa")
p.add_argument("caso", choices=["eventos", "error", "vectorlab"])
p.add_argument("script")
a = p.parse_args()
modo = {"eventos": "--p1", "error": "--p1-error", "vectorlab": "--p1-vectorlab"}
r = subprocess.run([a.programa, modo[a.caso], a.script], text=True,
                   capture_output=True, timeout=40)
sys.stdout.write(r.stdout)
sys.stderr.write(r.stderr)
informe = r.stdout + r.stderr
assert not re.search(r"AddressSanitizer|UndefinedBehaviorSanitizer|LeakSanitizer|runtime error:", informe)
assert r.returncode == 0, r.returncode
if a.caso == "error":
    assert "debe de ser un decimal" in r.stderr, r.stderr
    assert "la VM recuperó su estado" in r.stderr, r.stderr
    assert "se omite destructor" not in r.stderr, r.stderr
else:
    assert not r.stderr, r.stderr
print(json.dumps({"caso": a.caso, "status": "PASS"}))

"""Nombre del directorio local derivado del manifiesto de VS Code."""
import json
from pathlib import Path
import re
import sys

with Path(sys.argv[1]).open(encoding="utf-8") as stream:
    manifest = json.load(stream)
if (manifest["publisher"], manifest["name"]) != ("tuxmatic", "mictlan-language"):
    raise SystemExit("El manifiesto no corresponde a la extensión de Mictlán.")
version = manifest["version"]
if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+(?:-[a-zA-Z0-9.]+)?", version):
    raise SystemExit("Versión de la extensión inválida.")
print(f"{manifest['publisher']}.{manifest['name']}-{version}")

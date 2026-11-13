#!/usr/bin/env bash
set -euo pipefail

origen="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
identificador=$(python3 "$origen/identificador.py" "$origen/package.json")
destino="${MICTLAN_VSCODE_EXTENSIONS_DIR:-$HOME/.vscode/extensions}/$identificador"
if [[ ! -d "$destino" ]]; then
    echo "No hay instalación local de esta versión."
    exit 0
fi
if [[ -L "$destino" || ! -f "$destino/package.json" ]] ||
   [[ $(python3 "$origen/identificador.py" "$destino/package.json") != "$identificador" ]]; then
    echo "ERROR: carpeta inesperada; no se eliminó nada." >&2
    exit 1
fi
rm -r -- "$destino"
echo "OK: extensión local desinstalada. Recarga VS Code."

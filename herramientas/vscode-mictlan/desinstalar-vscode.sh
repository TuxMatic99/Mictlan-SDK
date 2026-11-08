#!/usr/bin/env bash
set -euo pipefail

destino="${HOME}/.vscode/extensions/tuxmatic.mictlan-language-0.1.0"
if [[ ! -d "$destino" ]]; then
    echo "No hay instalación local de esta versión."
    exit 0
fi
if [[ ! -f "$destino/package.json" ]] ||    ! grep -Fq '"name": "mictlan-language"' "$destino/package.json"; then
    echo "ERROR: carpeta inesperada; no se eliminó nada." >&2
    exit 1
fi
rm -r -- "$destino"
echo "OK: extensión local desinstalada. Recarga VS Code."

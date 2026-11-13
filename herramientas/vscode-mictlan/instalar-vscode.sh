#!/usr/bin/env bash
set -euo pipefail

origen="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
identificador=$(python3 "$origen/identificador.py" "$origen/package.json")
destino="${MICTLAN_VSCODE_EXTENSIONS_DIR:-$HOME/.vscode/extensions}/$identificador"
mkdir -p "$(dirname "$destino")"
if [[ -e "$destino" ]]; then
    echo "La extensión ya existe en: $destino" >&2
    echo "Para actualizarla, desinstala primero la versión anterior." >&2
    exit 1
fi

mkdir "$destino"
cp -a "$origen/package.json" "$origen/language-configuration.json" \
    "$origen/icons" "$origen/syntaxes" "$origen/LICENSE" "$origen/README.md" "$destino/"

echo "OK: extensión local instalada en $destino"
echo "En VS Code: Ctrl+Shift+P -> Developer: Reload Window"
echo "Abre un archivo .mict para probarla."

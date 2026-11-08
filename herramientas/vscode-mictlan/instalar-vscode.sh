#!/usr/bin/env bash
set -euo pipefail

origen="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
destino="${HOME}/.vscode/extensions/tuxmatic.mictlan-language-0.1.0"

if [[ ! -f "$origen/package.json" || ! -f "$origen/icons/mictlan-dark.png" ]]; then
    echo "ERROR: faltan archivos de la extensión." >&2
    exit 1
fi

mkdir -p "$(dirname "$destino")"
if [[ -e "$destino" ]]; then
    echo "La extensión ya existe en: $destino" >&2
    echo "Para actualizarla, desinstala primero la versión anterior." >&2
    exit 1
fi

mkdir "$destino"
cp -a "$origen/package.json" "$origen/language-configuration.json"       "$origen/icons" "$origen/syntaxes" "$destino/"

echo "OK: extensión local instalada en $destino"
echo "En VS Code: Ctrl+Shift+P -> Developer: Reload Window"
echo "Abre un archivo .mict para probarla."

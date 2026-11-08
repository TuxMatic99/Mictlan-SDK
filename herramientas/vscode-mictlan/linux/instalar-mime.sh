#!/usr/bin/env bash
set -euo pipefail

raiz="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
datos="${XDG_DATA_HOME:-$HOME/.local/share}"

if ! command -v update-mime-database >/dev/null 2>&1; then
    echo "Falta update-mime-database (shared-mime-info)." >&2
    exit 1
fi
mkdir -p "$datos/mime/packages"
cp "$raiz/linux/mictlan.xml" "$datos/mime/packages/mictlan.xml"

for tamano in 16 24 32 48 64 128 256; do
    lugar="$datos/icons/hicolor/${tamano}x${tamano}/mimetypes"
    mkdir -p "$lugar"
    cp "$raiz/icons/mictlan-light-${tamano}.png" "$lugar/text-x-mictlan.png"
done

update-mime-database "$datos/mime"
echo "OK: extensión .mict y símbolo MIME registrados para este usuario."
echo "Comprueba con: xdg-mime query filetype archivo.mict"
echo "El gestor de archivos puede requerir actualización de caché o reinicio."

#!/usr/bin/env bash
# Distribución de revisión en un directorio nuevo. No instala en el sistema.
set -euo pipefail
if [[ $# -lt 3 || $# -gt 4 ]]; then
    echo "Uso: bash preparar_alpha.sh CORE CORE_BUILD SALIDA_NUEVA [alpha01|p02g|p11]" >&2
    exit 3
fi
export LC_ALL=C.UTF-8
core=$(realpath "$1")
build=$(realpath "$2")
out=$(realpath -m "$3")
revision=${4:-alpha01}
case "$revision" in alpha01|p02g|p11) ;; *) exit 3 ;; esac
sdk=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd -P)
for source in "$core" "$sdk"; do
    [[ "$out" != "$source" && "$out" != "$source/"* ]]
    [[ -z "$(git -C "$source" status --porcelain)" ]]
done
[[ $(uname -s) == Linux && $(uname -m) == x86_64 ]]
core_sha=$(git -C "$core" rev-parse HEAD)
sdk_sha=$(git -C "$sdk" rev-parse HEAD)
python3 - "$sdk" "$core" "$build" "$core_sha" "$revision" <<'PY'
import json, pathlib, sys
sdk, core, build = map(pathlib.Path, sys.argv[1:4])
lock = json.loads((sdk / 'ci/p03/contrato.json').read_text())
cache = (build / 'CMakeCache.txt').read_text().splitlines()
if (sys.argv[4] != lock['core_revisions'][sys.argv[5]]['sha']
    or f'CMAKE_HOME_DIRECTORY:INTERNAL={core}' not in cache
    or 'CMAKE_BUILD_TYPE:STRING=Release' not in cache
    or any('-fsanitize=' in line for line in cache if line.startswith('CMAKE_'))):
    raise SystemExit('Se requiere el build Release exacto de Core para ' + sys.argv[5])
PY
mkdir -- "$out"
name=mictlan-alpha-p04-linux-x86_64
version=
if [[ "$revision" == alpha01 || "$revision" == p11 ]]; then
    identidad=$(env -u LD_LIBRARY_PATH -u LD_PRELOAD "$build/mictlan" --version)
    version=${identidad#Mictlán }
    [[ "$version" =~ ^[0-9]+\.[0-9]+\.[0-9]+(-[a-zA-Z0-9.]+)?$ ]]
    grep -Fx "#define MICTLAN_VERSION \"$version\"" "$core/include/mictlan_version.h" >/dev/null
    name="mictlan-$version-linux-x86_64"
fi
prefix="$out/armado/$name"
archive="$out/$name.zip"
cmake --install "$build" --prefix "$prefix" --component MictlanPortable
cmake --install "$build" --prefix "$prefix" --component Header
install -D -m 644 "$build/liblatino.so" "$prefix/lib/liblatino.so"
guia="$sdk/docs/p04/LEEME_ALPHA.md"
if [[ "$revision" == alpha01 || "$revision" == p11 ]]; then guia="$sdk/docs/alpha/INSTALAR.md"; fi
install -m 644 "$guia" "$prefix/README.md"
install -m 644 "$core/docs/p02g_contrato_memoria.md" "$prefix/CONTRATO_MEMORIA.md"
install -m 644 "$sdk/LICENSE" "$prefix/share/doc/mictlan/LICENSE-SDK"
install -m 644 "$sdk/include/"{mictlan_ciencia_ffi,mictlan_vectores2d}.h "$prefix/include/"
install -m 644 "$sdk/tests/datos/"{mictlan_ciencia_longitud,mictlan_suma_vectorial}.mict \
    "$prefix/share/mictlan/ejemplos/"
cc -std=c11 -O2 -I"$prefix/include" \
    "$sdk/src/ciencia/"{mictlan_ciencia_consola,mictlan_ciencia_ffi,vectores2d}.c \
    -L"$prefix/lib" -Wl,-rpath,'$ORIGIN/../lib' -llatino -lm -o "$prefix/bin/mictlan-ciencia"

if [[ "$revision" == alpha01 || "$revision" == p11 ]]; then
    install -m 644 "$core/docs/"{ESPECIFICACION_ALPHA,COMPATIBILIDAD,p02g_contrato_memoria}.md "$prefix/"
    install -m 644 "$core/ejemplos/resumen_cientifico.mict" "$prefix/share/mictlan/ejemplos/"
    mkdir -- "$prefix/herramientas"
    cp -a "$sdk/herramientas/vscode-mictlan" "$prefix/herramientas/"
    cp -a "$sdk/ejemplos/alpha-proyecto" "$prefix/proyecto"
    install -m 644 "$prefix/share/mictlan/ejemplos/hola_mictlan.mict" "$prefix/proyecto/primero.mict"
    install -m 644 "$sdk/ejemplos/mi_primera_ventana.lat" "$prefix/share/mictlan/ejemplos/"
fi

mkdir -- "$prefix/fuentes"
git -C "$core" archive --format=tar.gz --prefix=Mictlan-Core/ "$core_sha" > "$prefix/fuentes/Core.tar.gz"
git -C "$sdk" archive --format=tar.gz --prefix=Mictlan-SDK/ "$sdk_sha" > "$prefix/fuentes/SDK.tar.gz"
{
    printf 'Mictlán Alpha de consola\nCore %s\nSDK %s\n' "$core_sha" "$sdk_sha"
    uname -sm
    cat /etc/os-release
    cc --version
    cmake --version
    "$prefix/bin/mictlan" --version
    readelf -d "$prefix/bin/mictlan" "$prefix/lib/liblatino.so" "$prefix/bin/mictlan-ciencia"
} > "$prefix/VERSIONES.txt"
(
    cd -- "$prefix"
    find . -type f ! -name SHA256SUMS -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS
)
python3 - "$prefix" "$archive" <<'PY'
from pathlib import Path
import sys
from zipfile import ZipFile, ZIP_DEFLATED
root, dest = map(Path, sys.argv[1:])
with ZipFile(dest, 'x', compression=ZIP_DEFLATED, compresslevel=6) as archive:
    for item in sorted(root.rglob('*')):
        if item.is_file():
            archive.write(item, item.relative_to(root.parent))
PY

mkdir -- "$out/verificacion"
(
    cd -- "$out"
    sha256sum "$name.zip" > "$name.zip.sha256"
    sha256sum -c "$name.zip.sha256"
    unzip -q "$name.zip" -d verificacion
)
installed="$out/verificacion/$name"
(cd -- "$installed" && sha256sum -c SHA256SUMS) > "$out/archivos.log"
export -n LD_LIBRARY_PATH LD_PRELOAD
ldd -r "$installed/bin/mictlan-ciencia" > "$out/enlace.log" 2>&1
python3 - "$out/enlace.log" "$installed/lib/liblatino.so" <<'PY'
from pathlib import Path
import re, sys
text = Path(sys.argv[1]).read_text()
match = re.search(r'liblatino\.so => (.*?) \(', text)
if 'undefined symbol:' in text or 'not found' in text or not match or Path(match[1]).resolve() != Path(sys.argv[2]):
    raise SystemExit('El consumidor no se enlaza con la biblioteca extraída')
PY
ejemplos="$installed/share/mictlan/ejemplos"
(
    cd -- "$out/verificacion"
    timeout 30 "$installed/bin/mictlan" "$ejemplos/hola_mictlan.lat" > "$out/hola.log" 2> "$out/hola.err"
    timeout 30 "$installed/bin/mictlan-ciencia" "$ejemplos/mictlan_ciencia_longitud.mict" > "$out/longitud.log" 2> "$out/longitud.err"
    timeout 30 "$installed/bin/mictlan-ciencia" "$ejemplos/mictlan_suma_vectorial.mict" > "$out/suma.log" 2> "$out/suma.err"
)
for example in hola longitud suma; do
    test ! -s "$out/$example.err"
done
printf '%s\n' '¡Hola desde Mictlán!' 'Bienvenido a Mictlán' 'El resultado es: 42' | diff -u - "$out/hola.log"
printf '%s\n' 'Longitud del vector:' 5 | diff -u - "$out/longitud.log"
printf '%s\n' '=== SUMA VECTORIAL ===' 'Componente X:' 8 'Componente Y:' 16 \
    '=== SUMA DE CEROS ===' 0 0 '=== SIGNOS MIXTOS ===' 2 -8 '=== FIN ===' | diff -u - "$out/suma.log"
casos=3
if [[ "$revision" == alpha01 ]]; then
    "$installed/bin/mictlan" --version | tee "$out/version.log" | grep -Fx "Mictlán $version"
    "$installed/bin/mictlan" "$ejemplos/hola_mictlan.mict" > "$out/hola-mict.log" 2> "$out/hola-mict.err"
    test ! -s "$out/hola-mict.err"
    diff -u "$out/hola.log" "$out/hola-mict.log"
    "$installed/bin/mictlan-ciencia" "$ejemplos/resumen_cientifico.mict" > "$out/resumen.log" 2> "$out/resumen.err"
    test ! -s "$out/resumen.err"
    printf '%s\n' 'Mediciones: 3' 'Longitud total: 35' 'Promedio: 11.66666666666667' | diff -u - "$out/resumen.log"
    python3 "$sdk/tests/alpha/verificar_editor.py" "$installed" "$out/editor" > "$out/editor.log" 2>&1
    casos=7
fi
printf '{"status":"PASS","core_sha":"%s","sdk_sha":"%s","version":"%s","cases":%d}\n' \
    "$core_sha" "$sdk_sha" "$version" "$casos" > "$out/alpha.json"
printf 'Alpha verificada en carpeta aislada. %s\n' "$archive"

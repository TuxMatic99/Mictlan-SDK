#!/usr/bin/env bash
set -euo pipefail
if [[ $# -lt 3 ]]; then
    echo 'Uso: bash x11.sh PAQUETE SALIDA_NUEVA PERFIL [opciones de ventana.py]' >&2
    exit 3
fi
paquete=$(realpath "$1")
salida=$(realpath -m "$2")
perfil=$3
shift 3
raiz=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd -P)
mkdir -- "$salida"
for programa in xvfb-run openbox xdotool wmctrl; do
    if ! command -v "$programa" >/dev/null; then
        printf '{"status":"BLOCKED_INFRASTRUCTURE","falta":"%s"}\n' "$programa" > "$salida/ventana.json"
        exit 2
    fi
done
if xvfb-run -a --server-args='-screen 0 1440x900x24' bash -e -c '
    openbox > "$1/openbox.log" 2>&1 &
    pid=$!
    trap "kill $pid 2>/dev/null || true" EXIT
    for i in {1..30}; do
        wmctrl -m >/dev/null 2>&1 && break
        sleep 0.2
    done
    shift
    python3 "$@"
' bash "$salida" "$raiz/tests/p1/ventana.py" "$paquete" "$salida/casos" --perfil "$perfil" "$@" \
    > "$salida/x11.log" 2>&1; then
    cp "$salida/casos/ventana.json" "$salida/ventana.json"
else
    if [[ -f "$salida/casos/ventana.json" ]]; then
        cp "$salida/casos/ventana.json" "$salida/ventana.json"
    else
        printf '{"status":"BLOCKED_INFRASTRUCTURE","etapa":"inicio de Xvfb"}\n' > "$salida/ventana.json"
    fi
    cat "$salida/x11.log" >&2
    exit 1
fi

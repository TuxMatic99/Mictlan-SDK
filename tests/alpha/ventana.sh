#!/usr/bin/env bash
# Ejecutar en una pantalla X11 dedicada con un gestor de ventanas.
set -euo pipefail
if [[ $# != 2 ]]; then
    echo 'Uso: bash ventana.sh HOST_UI DIRECTORIO_NUEVO' >&2
    exit 3
fi
host=$(realpath "$1")
out=$(realpath -m "$2")
sdk=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd -P)
mkdir -- "$out"
resultado=FAIL_PROGRAM
pid=
limpiar() {
    local rc=$?
    if [[ -n "$pid" ]]; then kill "$pid" 2>/dev/null || true; wait "$pid" 2>/dev/null || true; fi
    printf '{"status":"%s","returncode":%d}\n' "$resultado" "$rc" > "$out/ventana.json"
}
trap limpiar EXIT
if ! command -v xdotool >/dev/null || ! command -v wmctrl >/dev/null ||
   ! wmctrl -m > "$out/gestor.log" 2>&1; then
    resultado=BLOCKED_INFRASTRUCTURE
    exit 2
fi
cp "$sdk/ejemplos/mi_primera_ventana.lat" "$out/mi_primera_ventana.mict"
cd "$out"
stdbuf -oL "$host" "$out/mi_primera_ventana.mict" > "$out/host.stdout.log" 2> "$out/host.stderr.log" &
pid=$!
ventana=$(timeout 12 xdotool search --sync --onlyvisible --pid "$pid" --name 'Mi primera aplicación')
[[ "$ventana" =~ ^[0-9]+$ ]]
xdotool getwindowname "$ventana" > "$out/titulo.log"
xdotool windowactivate --sync "$ventana"
[[ "$(xdotool getactivewindow)" == "$ventana" ]]
tecla() {
    printf 'Tecla %s en ventana %s\n' "$1" "$ventana" >> "$out/entrada.log"
    # Mantener la tecla durante varios cuadros para que Raylib lea el estado.
    xdotool keydown "$1"
    sleep 0.35
    xdotool keyup "$1"
    sleep 0.15
}
esperar_evento() {
    for ((i=0; i<50; i++)); do
        if grep -Fxq "$1" "$out/host.stdout.log"; then return 0; fi
        kill -0 "$pid"
        sleep 0.1
    done
    return 1
}
for ((i=0; i<100; i++)); do
    if grep -Fq 'Target time per frame:' "$out/host.stdout.log"; then break; fi
    kill -0 "$pid"
    sleep 0.1
done
grep -Fq 'Target time per frame:' "$out/host.stdout.log"
xdotool windowactivate --sync "$ventana"
sleep 0.35
tecla Return
esperar_evento 'Se pulsó Saludar'
tecla Tab
tecla Return
esperar_evento 'Se pulsó Despedirse'
printf 'Solicitud de cierre de ventana %s\n' "$ventana" >> "$out/entrada.log"
wmctrl -i -c "$(printf '0x%x' "$ventana")"
for ((i=0; i<50; i++)); do
    if ! kill -0 "$pid" 2>/dev/null; then break; fi
    sleep 0.1
done
if kill -0 "$pid" 2>/dev/null; then exit 1; fi
wait "$pid"
pid=
grep -F 'Window closed successfully' "$out/host.stdout.log"
if grep -Ei 'AddressSanitizer|UndefinedBehaviorSanitizer|LeakSanitizer|runtime error:|LatinoUI:' \
    "$out/host.stdout.log" "$out/host.stderr.log"; then exit 1; fi
resultado=PASS

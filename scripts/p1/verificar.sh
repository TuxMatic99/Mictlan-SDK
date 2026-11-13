#!/usr/bin/env bash
set -euo pipefail
if [[ $# != 5 ]]; then
    echo 'Uso: bash verificar.sh PERFIL CORE LAB RAYLIB DIRECTORIO_CI' >&2
    exit 3
fi
perfil=$1
core=$(realpath "$2")
lab=$(realpath "$3")
raylib=$(realpath "$4")
work=$(realpath "$5")
sdk=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd -P)
salida="$work/p1"
mkdir -- "$salida"
estado=FAIL_CONFIGURATION
terminar() {
    local rc=$?
    python3 - "$salida" "$estado" "$rc" <<'PY'
import json, pathlib, sys
d = pathlib.Path(sys.argv[1])
s = sys.argv[2]
for f in [d/'aplicaciones/aplicaciones.json', d/'ventana/ventana.json',
          d/'ventana-softpipe/ventana.json', d/'memoria/memoria.json']:
    if f.is_file():
        r = json.loads(f.read_text())['status']
        if r != 'PASS':
            s = r
            break
(d/'p1.json').write_text(json.dumps({'status': s, 'returncode': int(sys.argv[3])}, indent=2) + '\n')
PY
}
trap terminar EXIT
python3 - "$sdk" "$core" "$lab" "$raylib" "$work" "$perfil" <<'PY'
import json, pathlib, subprocess, sys
sdk, core, lab, raylib, work = map(pathlib.Path, sys.argv[1:6])
cfg = json.loads((sdk/'ci/p1/revisiones.json').read_text())
r = json.loads((work/'evidence/report.json').read_text())
if r['profile'] != sys.argv[6] or r['status'] != 'PASS' or r['identity'] != 'EXACT_COMMIT_PAIR':
    raise SystemExit('La batería de Core y SDK debe haber terminado correctamente')
for name, repo in [('core', core), ('lab', lab), ('raylib', raylib)]:
    sha = subprocess.check_output(['git','-C',repo,'rev-parse','HEAD'], text=True).strip()
    if sha != cfg[name] or subprocess.check_output(['git','-C',repo,'status','--porcelain']):
        raise SystemExit(f'Revisión inesperada: {name} {sha}')
PY
anterior=()
if [[ "$perfil" == release ]]; then
    estado=BLOCKED_INFRASTRUCTURE
    sdk_anterior_sha=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["sdk_comparacion"])' "$sdk/ci/p1/revisiones.json")
    git clone --quiet --no-checkout "$sdk" "$salida/sdk-anterior"
    git -C "$salida/sdk-anterior" checkout --quiet --detach "$sdk_anterior_sha"
    estado=FAIL_BUILD
    bash "$sdk/scripts/p1/compilar_anterior.sh" "$salida/sdk-anterior" "$core" \
        "$work/core/liblatino.so" "$work/sdk" "$salida/anterior" > "$salida/anterior-build.log" 2>&1
    anterior=(--anterior "$salida/anterior/carga_anterior")
fi
estado=FAIL_PROGRAM
python3 "$sdk/tests/p1/bateria.py" "$work/sdk" "$lab" "$salida/aplicaciones" --perfil "$perfil" "${anterior[@]}"
memoria=()
if [[ "$perfil" == sanitizers ]]; then memoria+=(--sanitizers); fi
if [[ "$perfil" == release ]]; then
    memoria+=(--larga)
    sha_base=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["sdk_p1"])' "$sdk/ci/p1/revisiones.json")
    mkdir -- "$salida/sdk-p1"
    git -C "$sdk" archive "$sha_base" | tar -x -C "$salida/sdk-p1"
    # Mismo anfitrión anterior. Solo se eleva el límite del backend de prueba.
    sed -i 's/n <= 10000/n <= 100000/' "$salida/sdk-p1/tests/test_ui_host.c"
    core_base="$core/../core-g"
    cmake -S "$salida/sdk-p1" -B "$salida/sdk-p1-build" -DCMAKE_BUILD_TYPE=Release \
        -DBUILD_TESTING=ON "-DCMAKE_PREFIX_PATH=$work/raylib-install" \
        "-DLATINO_INCLUDE_DIR=$core_base/include" "-DLATINO_LIBRARY=$work/core-g/liblatino.so" \
        > "$salida/sdk-p1-build.log" 2>&1
    cmake --build "$salida/sdk-p1-build" --parallel 2 --target test_ui_host \
        >> "$salida/sdk-p1-build.log" 2>&1
    memoria+=(--base "$salida/sdk-p1-build/test_ui_host")
fi
python3 "$sdk/tests/p1/memoria.py" "$work/sdk/test_ui_host" "$lab" "$salida/memoria" "${memoria[@]}"

if [[ "$perfil" == release ]]; then
    estado=FAIL_PACKAGE
    python3 "$sdk/scripts/p1/preparar_paquete.py" --core "$core" --core-build "$work/core" \
        --sdk-build "$work/sdk" --lab "$lab" --raylib "$raylib" \
        --raylib-lib "$work/raylib-install/lib/libraylib.so.550" --output "$salida/paquete" \
        > "$salida/paquete.log" 2>&1
    prefijo=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["extraido"])' "$salida/paquete/paquete.json")
    estado=FAIL_EDITOR
    python3 "$sdk/tests/p1/vscode.py" "$prefijo" "$salida/vscode"
    estado=FAIL_GUI
    bash "$sdk/scripts/p1/x11.sh" "$prefijo" "$salida/ventana" release \
        --anterior "$salida/anterior/sdk/host_ui" --capturas
elif [[ "$perfil" == sanitizers ]]; then
    estado=FAIL_GUI
    fuente="$salida/fuentes-graficas"
    mkdir -p "$fuente/share/mictlan/ejemplos"
    cp "$sdk/ejemplos/p1/contador.mict" "$fuente/share/mictlan/ejemplos/"
    ln -s "$lab/VectorLab" "$fuente/VectorLab"
    ln -s "$lab/Registro" "$fuente/Registro"
    control="$salida/raylib-control"
    estado=FAIL_BUILD
    cc -std=c11 -g -O0 -fsanitize=address,undefined -fno-sanitize-recover=all \
       -fno-omit-frame-pointer -I"$work/raylib-install/include" "$sdk/tests/p1/raylib_control.c" \
       -L"$work/raylib-install/lib" -Wl,-rpath,"$work/raylib-install/lib" -lraylib -o "$control"
    estado=FAIL_GUI
    bash "$sdk/scripts/p1/x11.sh" "$fuente" "$salida/ventana" sanitizers \
        --host "$work/sdk/host_ui" --control-raylib "$control" || estado=FAIL_GUI
    bash "$sdk/scripts/p1/x11.sh" "$fuente" "$salida/ventana-softpipe" sanitizers \
        --host "$work/sdk/host_ui" --control-raylib "$control" --driver softpipe || estado=FAIL_GUI
    python3 "$sdk/tests/p1/mesa.py" "$salida" "$salida/mesa"
    python3 - "$salida" <<'PY'
import json, pathlib, sys
base = pathlib.Path(sys.argv[1])
fallos = []
for d in ("ventana", "ventana-softpipe"):
    r = json.loads((base / d / "ventana.json").read_text())
    print(d, r["status"], {k:v["status"] for k,v in r.get("cases", {}).items()})
    if r["status"] != "PASS":
        fallos.append(r["status"])
if fallos:
    raise SystemExit(', '.join(fallos))
PY
fi
estado=PASS

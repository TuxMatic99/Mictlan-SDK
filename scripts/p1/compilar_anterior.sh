#!/usr/bin/env bash
# Compila el host publicado de Alpha y usa el mismo dispositivo simulado.
set -euo pipefail
if [[ $# != 5 ]]; then
    echo 'Uso: bash compilar_anterior.sh SDK_ANTERIOR CORE LIBLATINO SDK_BUILD SALIDA_NUEVA' >&2
    exit 3
fi
anterior=$(realpath "$1")
core=$(realpath "$2")
biblioteca=$(realpath "$3")
actual=$(realpath "$4")
salida=$(realpath -m "$5")
sdk=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd -P)
mkdir -- "$salida"
raylib=$(sed -n 's/^raylib_DIR:[^=]*=//p' "$actual/CMakeCache.txt")
test -n "$raylib"
prefijo=$(sed -n 's/^CMAKE_PREFIX_PATH:[^=]*=//p' "$actual/CMakeCache.txt")
cmake -S "$anterior" -B "$salida/sdk" -DCMAKE_BUILD_TYPE=Release \
    "-DLATINO_INCLUDE_DIR=$core/include" "-DLATINO_LIBRARY=$biblioteca" \
    "-Draylib_DIR=$raylib" "-DCMAKE_PREFIX_PATH=$prefijo"
cmake --build "$salida/sdk" --parallel 2 --target host_ui host_ui_para_pruebas
python3 - "$anterior/src/ui/host_ui.c" "$salida/host_anterior.c" <<'PY'
import pathlib, sys
s = pathlib.Path(sys.argv[1]).read_text()
s = s.replace('    bool aviso_vm_comprometida = false;',
'''    double medicion_inicio;
    ui_despachador_reloj_monotonico(NULL, &medicion_inicio);
    size_t medicion_cuadros = 0;
    bool aviso_vm_comprometida = false;''')
s = s.replace('        EndDrawing();', '        EndDrawing();\n        ++medicion_cuadros;')
insercion = r'''    if (getenv("MICTLAN_UI_METRICAS")) {
        double medicion_fin;
        ui_despachador_reloj_monotonico(NULL, &medicion_fin);
        printf("MICTLAN_UI_METRICAS {\"cuadros\":%zu,\"eventos_entregados\":%zu,"
               "\"callback_max_ms\":%.6f,\"ms\":%.6f,\"bytes_vm\":%zu,\"cadenas\":%u}\n",
               medicion_cuadros, despachador.metricas.eventos_despachados,
               despachador.metricas.max_callback_ms, medicion_fin - medicion_inicio,
               mv->memoria_usada, mv->global->strt.nuse);
    }
'''
marca = '    salida = EXIT_SUCCESS;\n\ncerrar:'
assert s.count(marca) == 1 and s.count('++medicion_cuadros') == 1
pathlib.Path(sys.argv[2]).write_text(s.replace(marca, insercion + marca))
PY
lib="$salida/sdk"
cc -std=c11 -O3 -DMICTLAN_HOST_PRUEBAS -Dmain=latino_ui_host_main \
    -I"$anterior/tests/soporte_host" -I"$anterior/include" -I"$core/include" \
    -c "$salida/host_anterior.c" -o "$salida/host_anterior.o"
cc -std=c11 -O3 -I"$anterior/tests/soporte_host" -I"$anterior/include" -I"$core/include" \
    "$sdk/tests/test_ui_host.c" "$salida/host_anterior.o" \
    -Wl,--start-group "$lib"/lib*.a -Wl,--end-group "$biblioteca" \
    -Wl,-rpath,"$(dirname -- "$biblioteca")" -lm -o "$salida/carga_anterior"

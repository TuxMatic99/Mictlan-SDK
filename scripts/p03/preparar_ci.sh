#!/usr/bin/env bash
# Compilar copias de CI en directorios nuevos; nunca instala ni edita Core.
set -Eeuo pipefail
if [[ $# -lt 5 || $# -gt 6 ]]; then
    echo "Uso: bash preparar_ci.sh debug|release|sanitizers CORE RAYLIB TRABAJO_NUEVO SDK_SHA [REVISION_EN_CONTRATO]" >&2
    exit 3
fi
profile=$1
core=$(realpath "$2")
raylib=$(realpath "$3")
work=$(realpath -m "$4")
sdk_sha=$5
revision=${6:-p02e}
sdk=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd -P)
case "$profile" in debug|release|sanitizers) ;; *) exit 3 ;; esac
export GIT_OPTIONAL_LOCKS=0
# Validar antes de escribir o compilar; las copias deben estar limpias.
if ! python3 - "$sdk" "$core" "$raylib" "$work" "$sdk_sha" "$revision" <<'PY'
import json, pathlib, re, subprocess, sys
sdk, core, raylib, work = map(pathlib.Path, sys.argv[1:5])
expected_sdk = sys.argv[5]
lock = json.loads((sdk / 'ci/p03/contrato.json').read_text())
def require(condition, message):
    if not condition: raise SystemExit(message)
require(re.fullmatch(r'[0-9a-f]{40}', expected_sdk), 'SHA SDK completo requerido')
require(not work.exists(), 'Usar un directorio de trabajo nuevo')
for path, expected in [(sdk, expected_sdk), (core, lock['core_revisions'][sys.argv[6]]['sha']), (raylib, lock['raylib_sha'])]:
    require(work != path and path not in work.parents, 'Build dentro de fuentes prohibido')
    actual = subprocess.check_output(['git', '-C', str(path), 'rev-parse', 'HEAD'], text=True).strip()
    require(actual == expected, f'SHA inesperado: {path}')
    require(not subprocess.check_output(['git', '-C', str(path), 'status', '--porcelain']), f'Arbol modificado: {path}')
PY
then
    exit 3
fi
mkdir -- "$work"
exec > >(tee "$work/preparation.log") 2>&1
stage=build
finish() {
    local result=$?
    python3 - "$work" "$stage" "$result" <<'PY'
import datetime, json, pathlib, sys
record = {'phase': sys.argv[2], 'exitcode': int(sys.argv[3]),
          'finished_utc': datetime.datetime.now(datetime.timezone.utc).isoformat()}
(pathlib.Path(sys.argv[1]) / 'preparation.json').write_text(json.dumps(record, indent=2) + '\n')
PY
    exit "$result"
}
trap finish EXIT
dpkg-query -W > "$work/packages.txt"
cmake --version
ctest --version
gcc --version
build_type=Debug
flags='-O0 -g'
if [[ "$profile" == release ]]; then build_type=Release; flags='-g'; fi
link_flags=''
if [[ "$profile" == sanitizers ]]; then
    flags+=' -fsanitize=address,undefined -fno-sanitize-recover=all -fno-omit-frame-pointer'
    link_flags='-fsanitize=address,undefined'
fi
cmake -S "$raylib" -B "$work/raylib-build" -DCMAKE_BUILD_TYPE=Release \
    -DBUILD_EXAMPLES=OFF -DBUILD_SHARED_LIBS=ON -DCMAKE_INSTALL_PREFIX="$work/raylib-install"
cmake --build "$work/raylib-build" --parallel 2
cmake --install "$work/raylib-build"
cmake -S "$core" -B "$work/core" "-DCMAKE_BUILD_TYPE=$build_type" \
    -DCMAKE_C_COMPILER=gcc -DCMAKE_CXX_COMPILER=g++ -DCMAKE_EXPORT_COMPILE_COMMANDS=ON \
    "-DCMAKE_C_FLAGS=$flags" "-DCMAKE_CXX_FLAGS=$flags" "-DCMAKE_EXE_LINKER_FLAGS=$link_flags" \
    "-DCMAKE_SHARED_LINKER_FLAGS=$link_flags"
cmake --build "$work/core" --parallel 2
for component in sdk vm integration; do
    source=$sdk
    if [[ "$component" == vm ]]; then source="$sdk/tests/p03_vm"; fi
    if [[ "$component" == integration ]]; then source="$sdk/tests/p03_integration"; fi
    cmake -S "$source" -B "$work/$component" "-DCMAKE_BUILD_TYPE=$build_type" \
        -DCMAKE_C_COMPILER=gcc -DCMAKE_EXPORT_COMPILE_COMMANDS=ON -DBUILD_TESTING=ON \
        "-DCMAKE_C_FLAGS=$flags" "-DCMAKE_CXX_FLAGS=$flags" "-DCMAKE_EXE_LINKER_FLAGS=$link_flags" \
        "-DCMAKE_SHARED_LINKER_FLAGS=$link_flags" \
        "-DCMAKE_PREFIX_PATH=$work/raylib-install" \
        "-DLATINO_INCLUDE_DIR=$core/include" "-DLATINO_LIBRARY=$work/core/liblatino.so"
    cmake --build "$work/$component" --parallel 2
done
cmake -S "$sdk/tests/p03" -B "$work/verifiers"
stage=tests
python3 "$sdk/tests/p03_ci/probar_resultados.py"
python3 "$sdk/tests/p03_ci/probar_core.py"
python3 "$sdk/scripts/p03/ejecutar_bateria.py" \
    --sdk-build "$work/sdk" --core-source "$core" --core-build "$work/core" \
    --vm-build "$work/vm" --integration-build "$work/integration" --verifiers-build "$work/verifiers" \
    --profile "$profile" --core-revision "$revision" --expected-sdk-sha "$sdk_sha" --output "$work/evidence"

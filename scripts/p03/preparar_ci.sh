#!/usr/bin/env bash
# Compilar copias de CI en directorios nuevos; nunca instala ni edita Core.
set -Eeuo pipefail
if [[ $# -ne 5 ]]; then
    echo "Uso: bash preparar_ci.sh debug|sanitizers CORE RAYLIB TRABAJO_NUEVO SDK_SHA" >&2
    exit 3
fi
profile=$1
core=$(realpath "$2")
raylib=$(realpath "$3")
work=$(realpath -m "$4")
sdk_sha=$5
sdk=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd -P)
case "$profile" in debug|sanitizers) ;; *) exit 3 ;; esac
export GIT_OPTIONAL_LOCKS=0
# Validar antes de escribir o compilar; las copias deben estar limpias.
if ! python3 - "$sdk" "$core" "$raylib" "$work" "$sdk_sha" <<'PY'
import json, pathlib, re, subprocess, sys
sdk, core, raylib, work = map(pathlib.Path, sys.argv[1:5])
expected_sdk = sys.argv[5]
lock = json.loads((sdk / 'ci/p03/contrato.json').read_text())
assert re.fullmatch(r'[0-9a-f]{40}', expected_sdk), 'SHA SDK completo requerido'
assert not work.exists(), 'Usar un directorio de trabajo nuevo'
for path, expected in [(sdk, expected_sdk), (core, lock['core_sha']), (raylib, lock['raylib_sha'])]:
    assert work != path and path not in work.parents, 'Build dentro de fuentes prohibido'
    actual = subprocess.check_output(['git', '-C', str(path), 'rev-parse', 'HEAD'], text=True).strip()
    assert actual == expected, f'SHA inesperado: {path}'
    assert not subprocess.check_output(['git', '-C', str(path), 'status', '--porcelain']), f'Arbol modificado: {path}'
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
flags='-O0 -g'
link_flags=''
if [[ "$profile" == sanitizers ]]; then
    flags+=' -fsanitize=address,undefined -fno-sanitize-recover=all -fno-omit-frame-pointer'
    link_flags='-fsanitize=address,undefined'
fi
cmake -S "$raylib" -B "$work/raylib-build" -DCMAKE_BUILD_TYPE=Release \
    -DBUILD_EXAMPLES=OFF -DBUILD_SHARED_LIBS=ON -DCMAKE_INSTALL_PREFIX="$work/raylib-install"
cmake --build "$work/raylib-build" --parallel 2
cmake --install "$work/raylib-build"
cmake -S "$core" -B "$work/core" -DCMAKE_BUILD_TYPE=Debug \
    -DCMAKE_C_COMPILER=gcc -DCMAKE_CXX_COMPILER=g++ \
    "-DCMAKE_C_FLAGS=$flags" "-DCMAKE_EXE_LINKER_FLAGS=$link_flags" \
    "-DCMAKE_SHARED_LINKER_FLAGS=$link_flags"
cmake --build "$work/core" --target liblatino --parallel 2
for component in sdk vm; do
    source=$sdk
    if [[ "$component" == vm ]]; then source="$sdk/tests/p03_vm"; fi
    cmake -S "$source" -B "$work/$component" -DCMAKE_BUILD_TYPE=Debug \
        -DCMAKE_C_COMPILER=gcc -DCMAKE_EXPORT_COMPILE_COMMANDS=ON -DBUILD_TESTING=ON \
        "-DCMAKE_C_FLAGS=$flags" "-DCMAKE_EXE_LINKER_FLAGS=$link_flags" \
        "-DCMAKE_SHARED_LINKER_FLAGS=$link_flags" \
        "-DCMAKE_PREFIX_PATH=$work/raylib-install" \
        "-DLATINO_INCLUDE_DIR=$core/include" "-DLATINO_LIBRARY=$work/core/liblatino.so"
    cmake --build "$work/$component" --parallel 2
done
cmake -S "$sdk/tests/p03" -B "$work/verifiers"
stage=tests
python3 "$sdk/tests/p03_ci/probar_resultados.py"
python3 "$sdk/scripts/p03/ejecutar_bateria.py" \
    --sdk-build "$work/sdk" --core-source "$core" --core-build "$work/core" \
    --vm-build "$work/vm" --verifiers-build "$work/verifiers" \
    --profile "$profile" --expected-sdk-sha "$sdk_sha" --output "$work/evidence"

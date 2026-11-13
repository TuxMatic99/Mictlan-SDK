# Reproducir P0.2-G y P0.4 en Debian 13

Usa un directorio nuevo para preservar tus ramas y compilaciones. Los comandos necesitan GitHub y permiso de lectura de los repositorios. Las compilaciones se guardan en carpetas separadas.

```bash
sudo apt update
sudo apt install git build-essential cmake python3 binutils pkg-config \
  libreadline-dev xorg-dev libgl1-mesa-dev unzip
mkdir -p ~/mictlan-revision-p04
cd ~/mictlan-revision-p04
git clone --branch verificacion/p02g-memoria-alpha https://github.com/TuxMatic99/Mictlan-SDK.git sdk
git clone https://github.com/TuxMatic99/Mictlan-Core.git core
git clone https://github.com/TuxMatic99/Mictlan-Core.git core-fe
git clone https://github.com/raysan5/raylib.git raylib
```

Para repetir una ejecución concreta, fija primero el SDK con `git -C sdk checkout --detach SHA_DEL_INFORME`. Selecciona las dependencias exactas de ese SDK.

```bash
python3 - <<'PY'
import json, subprocess
with open("sdk/ci/p03/contrato.json") as f:
    lock = json.load(f)
g = lock["core_revisions"]["p02g"]
for folder, sha in [
    ("core", g["sha"]),
    ("core-fe", lock["core_revisions"][g["stress"]["base"]]["sha"]),
    ("raylib", lock["raylib_sha"]),
]:
    subprocess.run(["git", "-C", folder, "checkout", "--detach", sha], check=True)
PY

sdk_sha=$(git -C sdk rev-parse HEAD)
bash sdk/scripts/p03/preparar_ci.sh debug core raylib run-debug "$sdk_sha" p02g
bash sdk/scripts/p03/preparar_ci.sh release core raylib run-release "$sdk_sha" p02g
bash sdk/scripts/p03/preparar_ci.sh sanitizers core raylib run-sanitizers "$sdk_sha" p02g
```

CMake y CTest deben ser 3.26 o superiores. Cada ejecución guarda sus comandos, trazas, huellas de archivos, JSON y JUnit en `run-*/evidence`. Si repites una ejecución, elige un nombre de salida distinto. La prueba de 100.000 operaciones requiere varios cientos de MiB de memoria libre para la revisión F+E. Debug y sanitizadores ejecutan hasta 10.000.

## Interpretar el resultado

| Estado | Significado |
| --- | --- |
| `PASS` | Las comprobaciones exigidas de ese perfil terminaron correctamente. |
| `FAIL_PROGRAM` | Una comprobación de estado o resultados falló. |
| `FAIL_SANITIZER` | La salida contiene un diagnóstico de memoria o de comportamiento indefinido. |
| `INVALID_CONFIG` | La revisión, los símbolos, las dependencias o el inventario difieren del contrato. |
| `BLOCKED_INFRASTRUCTURE` | El entorno impidió comprobar, por ejemplo, LeakSanitizer bajo una restricción de `ptrace`. |

Ejecuta el perfil instrumentado desde la terminal, fuera de depuradores y trazadores. El control limpio de LSan debe terminar con código cero. El control con una fuga debe informar esa fuga y devolver el código esperado. ASan y UBSan tienen controles propios. GitHub Actions usa un runner Linux hospedado y conserva las trazas aun cuando el trabajo falla.

## Generar el paquete Alpha

Después de verificar Release, ejecuta lo siguiente desde el mismo directorio.

```bash
bash sdk/scripts/p04/preparar_alpha.sh core run-release/core alpha-p04
```

El ZIP contiene un ejecutor general, el ejecutor científico, la biblioteca y sus cabeceras. El script lo extrae en una carpeta separada, verifica las sumas SHA-256 y compara las salidas de tres ejemplos. Consulta la [guía de Alpha](LEEME_ALPHA.md) para el primer programa y la conexión al SDK.

# Reproducir Mictlán Alpha 0.1

Los comandos crean copias y compilaciones separadas. El informe y las PR fijan los SHA completos. Selecciona el SHA del SDK del informe si quieres repetir una ejecución anterior.

```bash
sudo apt install git build-essential cmake python3 binutils pkg-config \
  libreadline-dev xorg-dev libgl1-mesa-dev unzip shared-mime-info libglib2.0-bin
mkdir ~/mictlan-alpha-revision
cd ~/mictlan-alpha-revision
git clone --branch consolidacion/alpha-0.1-sdk https://github.com/TuxMatic99/Mictlan-SDK.git sdk
git clone https://github.com/TuxMatic99/Mictlan-Core.git core
git clone https://github.com/TuxMatic99/Mictlan-Core.git core-fe
git clone https://github.com/TuxMatic99/Mictlan-Core.git core-g
git clone https://github.com/raysan5/raylib.git raylib
```

```bash
python3 - <<'PY'
import json, subprocess
with open("sdk/ci/p03/contrato.json") as f:
    lock = json.load(f)
revs = lock["core_revisions"]
for carpeta, sha in [
    ("core", revs["alpha01"]["sha"]),
    ("core-fe", revs["p02f_e"]["sha"]),
    ("core-g", revs["p02g"]["sha"]),
    ("raylib", lock["raylib_sha"]),
]:
    subprocess.run(["git", "-C", carpeta, "checkout", "--detach", sha], check=True)
PY
sdk_sha=$(git -C sdk rev-parse HEAD)
bash sdk/scripts/p03/preparar_ci.sh debug core raylib salida-debug "$sdk_sha" alpha01
bash sdk/scripts/p03/preparar_ci.sh release core raylib salida-release "$sdk_sha" alpha01
bash sdk/scripts/p03/preparar_ci.sh sanitizers core raylib salida-sanitizers "$sdk_sha" alpha01
bash sdk/scripts/p04/preparar_alpha.sh core salida-release/core paquete alpha01
```

CMake y CTest deben ser 3.26 o superiores. Los informes se guardan en `salida-*/evidence/report.json` y sus XML JUnit. `BLOCKED_INFRASTRUCTURE` indica que faltó una capacidad del entorno. Ejecuta LSan fuera de depuradores y conserva los diagnósticos si informa un bloqueo de `ptrace`. En Release la comparación de memoria incluye una sesión de 60 segundos con el recolector activado. Las cargas de la base y el candidato usan el mismo ejecutable de prueba. Los números de memoria del proceso y de la VM tienen unidades y alcances distintos.

La prueba gráfica usa un servidor X11 virtual, Raylib y un gestor de ventanas. La infraestructura de CI abre la aplicación, envía Enter y Tab, comprueba los dos eventos y solicita el cierre. En tu escritorio puedes ejecutar el ejemplo descrito en el README. [Configuración de CI](../../.github/workflows/p03.yml).

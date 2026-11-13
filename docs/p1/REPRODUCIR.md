# Reproducción de Mictlán Applications Alpha

El contrato conserva la matriz de Core y SDK de Alpha 0.1. P1 añade el programa de Lab fijado en `ci/p1/revisiones.json`. El informe de GitHub muestra ambas etapas y guarda los comandos, informes JSON, XML y trazas. En Release se compara con SDK Alpha 0.1 usando el mismo Core, Raylib y carga de callbacks.

## Preparar copias en Debian 13

```bash
sudo apt install git build-essential cmake python3 binutils pkg-config libreadline-dev \
  xorg-dev libgl1-mesa-dev libgl1-mesa-dri shared-mime-info libglib2.0-bin unzip \
  xvfb xauth openbox xdotool wmctrl imagemagick
mkdir ~/revisar-mictlan-p1
cd ~/revisar-mictlan-p1
git clone --branch aplicaciones/p1-distribucion https://github.com/TuxMatic99/Mictlan-SDK.git sdk
git clone https://github.com/TuxMatic99/Mictlan-Core.git core
git clone https://github.com/TuxMatic99/Mictlan-Core.git core-fe
git clone https://github.com/TuxMatic99/Mictlan-Core.git core-g
git clone https://github.com/TuxMatic99/Mictlan-Lab.git lab
git clone https://github.com/raysan5/raylib.git raylib
```

Usa el SHA del SDK que indica el informe para repetir exactamente la entrega. El siguiente paso fija las otras copias.

```bash
python3 - <<'PY'
import json, subprocess
p1 = json.load(open("sdk/ci/p1/revisiones.json"))
core = json.load(open("sdk/ci/p03/contrato.json"))["core_revisions"]
for nombre, sha in [("core", p1["core"]), ("core-fe", core["p02f_e"]["sha"]),
                    ("core-g", core["p02g"]["sha"]), ("lab", p1["lab"]), ("raylib", p1["raylib"])]:
    subprocess.run(["git", "-C", nombre, "checkout", "--detach", sha], check=True)
PY
sdk_sha=$(git -C sdk rev-parse HEAD)
for perfil in debug release sanitizers; do
  bash sdk/scripts/p03/preparar_ci.sh "$perfil" core raylib "salida-$perfil" "$sdk_sha" alpha01 || exit
  bash sdk/scripts/p1/verificar.sh "$perfil" core lab raylib "salida-$perfil" || exit
done
```

Cada directorio de salida debe ser nuevo. `evidence/report.json` contiene el contrato anterior y `p1/p1.json` la aceptación de P1. Release agrega la prueba de los dos ejecutables de consola, enlace del paquete, tareas de VS Code y ventana real con X11 virtual. El perfil instrumentado ejecuta Core y SDK con ASan y UBSan y detección de fugas activa, más un control LSan independiente. `BLOCKED_INFRASTRUCTURE` indica que una capacidad del entorno impidió completar la prueba.

La prueba gráfica registra resultados del ratón, teclado, cambio de tamaño, color del plano y cierre. Los tiempos de carga de CTest se miden con un backend determinista que usa Core y callbacks reales. Los FPS solo corresponden a Raylib con ventana. El presupuesto de carga gráfica es 60 eventos y al menos 18 segundos por anfitrión. [Guía de escritorio físico](DISTRIBUCION.md).

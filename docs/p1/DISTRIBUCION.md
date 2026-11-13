# Mictlán Applications Alpha

Paquete experimental para Debian 13 x86_64. Incluye la consola, el anfitrión gráfico, Raylib 5.5, la biblioteca de Core y VectorLab. `VERSIONES.json` identifica los SHA exactos. Los ejecutables buscan las bibliotecas incluidas junto al prefijo extraído.

## Abrir VectorLab

En un Debian con escritorio instala las dependencias que falten.

```bash
sudo apt install unzip libreadline8t64 libgl1 libgl1-mesa-dri libx11-6 libxrandr2 libxi6 libxcursor1 libxinerama1
unzip mictlan-aplicaciones-0.1.0-alpha-linux-x86_64.zip
cd mictlan-aplicaciones-0.1.0-alpha-linux-x86_64
sha256sum -c SHA256SUMS
./bin/mictlan --version
./bin/mictlan-ui --version
./bin/probar-vectorlab
cd VectorLab
../bin/mictlan-ui -- principal.mict
```

Edita Ax, Ay, Bx o By. Pulsa Enter o Calcular. Tab y Mayús+Tab cambian el foco. Guardar y Cargar usan `vectorlab-v1.txt` en la carpeta de trabajo. La guía del formato está en `VectorLab/README.md`. Conserva ese archivo si deseas preservar tu sesión al retirar la carpeta extraída.

El intérprete `bin/mictlan` funciona en terminal sin Raylib ni un servidor X. Ejecuta `bin/mictlan share/mictlan/ejemplos/hola_mictlan.mict` desde la raíz. Para otra aplicación abre `share/mictlan/ejemplos/contador.mict` con `bin/mictlan-ui`. Cambia sus controles y acciones en el archivo. El anfitrión permanece genérico.

## VS Code

Desde la raíz del paquete ejecuta `bash herramientas/vscode-mictlan/instalar-vscode.sh` con Python 3 instalado. Recarga VS Code y abre la carpeta `VectorLab`. En **Terminal > Ejecutar tarea** aparecen Consola, Aplicación gráfica y Pruebas de VectorLab. La consola ejecuta el archivo activo. La tarea gráfica abre `principal.mict`. La de pruebas calcula casos y verifica una sesión en una carpeta temporal. Los diagnósticos de Core con ruta, línea y columna aparecen en Problemas. El resaltado y los iconos se instalan con la extensión incluida.

## Revisión en un escritorio Debian

1. Comprueba los hashes y las dos versiones. Ejecuta las pruebas de VectorLab.
2. Abre la aplicación y verifica las magnitudes 5 y 13, la suma (8, 16), la resta (−2, −8) y el producto punto 63.
3. Cambia Ax de 3 a 0 usando el teclado. Pulsa Enter y comprueba 48. Introduce texto inválido y comprueba el aviso y el último resultado.
4. Guarda los vectores, modifica una componente y recupera el archivo con el ratón. Redimensiona. Comprueba que el plano conserva la misma escala en X e Y. Prueba Tab, Mayús+Tab y el botón de cierre del gestor de ventanas.
5. Repite con la tarea de VS Code. Para verificar Problemas, ejecuta un archivo temporal que contenga `escribir(sin_definir)`. El diagnóstico debe señalar el archivo y la posición del nombre.

La validación automatizada usa X11 virtual y Mesa por software. La revisión física debe guardar versión del sistema, gestor de ventanas, salida de la terminal y cualquier diferencia observada. Para retirar la extensión usa `bash herramientas/vscode-mictlan/desinstalar-vscode.sh`. El paquete se retira eliminando la carpeta extraída después de guardar los proyectos que quieras conservar.

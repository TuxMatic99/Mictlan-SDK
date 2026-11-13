# Mictlán Alpha de consola en Debian

Paquete para Debian 13 x86_64. El archivo `VERSIONES.txt` identifica la versión de producto, Core y SDK. El ZIP contiene `mictlan`, `mictlan-ciencia`, la biblioteca `liblatino.so`, cabeceras, licencias, fuentes y ejemplos. Los ejecutores conservan el ciclo de vida de memoria F de forma predeterminada.

## Extraer y ejecutar

En Debian, instala las dependencias que falten.

```bash
sudo apt install libreadline8t64 unzip
unzip mictlan-0.1.0-alpha-linux-x86_64.zip
cd mictlan-0.1.0-alpha-linux-x86_64
sha256sum -c SHA256SUMS
./bin/mictlan --version
./bin/mictlan share/mictlan/ejemplos/hola_mictlan.mict
```

El ejemplo termina en 42. Para crear tu programa, abre un editor de texto y guarda lo siguiente como `primero.mict`.

```mictlan
nombre = "Mictlán"
escribir("Hola desde " .. nombre)
```

Ejecuta `./bin/mictlan primero.mict`. Un programa heredado se ejecuta con `./bin/mictlan archivo.lat`. Si la ruta contiene espacios, ponla entre comillas. La consola muestra el archivo, línea y columna en los errores de código.

## Ciencia sin cambiar el anfitrión

```bash
./bin/mictlan-ciencia share/mictlan/ejemplos/resumen_cientifico.mict
```

El programa calcula el total 35 y el promedio de las longitudes de tres vectores. Copia ese archivo y cambia la lista de muestras para hacer tu propia aplicación. El ejecutor registra las funciones `longitud2`, `producto_punto2` y `sumar2` del módulo `ciencia`. Consulta `ESPECIFICACION_ALPHA.md` para la sintaxis y `COMPATIBILIDAD.md` para módulos, archivos y ABI.

## VS Code y el icono de Linux

Con VS Code y Python 3 instalados, puedes activar la extensión incluida.

```bash
bash herramientas/vscode-mictlan/instalar-vscode.sh
```

Recarga la ventana de VS Code y abre la carpeta `proyecto` del paquete. Con `primero.mict` activo, elige **Terminal > Ejecutar tarea > Mictlán ejecutar archivo activo**. La tarea local usa el ejecutor de esta copia. Si VS Code pide confianza del área de trabajo, comprueba que abriste tu copia del paquete antes de habilitar tareas.

En Linux, puedes registrar el icono y el tipo MIME de `.mict` para tu usuario con `bash herramientas/vscode-mictlan/linux/instalar-mime.sh`. Requiere `shared-mime-info`. En proyectos con `.lat`, elige el modo de lenguaje Mictlán o configura la asociación solo para ese proyecto.

## Gráficos y desarrollo del SDK

El ejemplo gráfico se ejecuta con `host_ui` del SDK compilado. El ZIP de consola conserva el código del ejemplo. Los binarios gráficos se compilan con Raylib por separado. Para enlazar el SDK, usa las rutas absolutas de `include` y `lib/liblatino.so` y el prefijo de Raylib fijado por la guía de reproducción.

```bash
tar -xzf fuentes/SDK.tar.gz
cmake -S Mictlan-SDK -B sdk-build -DCMAKE_BUILD_TYPE=Release \
  -DLATINO_INCLUDE_DIR="$PWD/include" -DLATINO_LIBRARY="$PWD/lib/liblatino.so" \
  -DCMAKE_PREFIX_PATH=/ruta/a/raylib-instalado
cmake --build sdk-build --parallel 2
ctest --test-dir sdk-build --output-on-failure
```

Si falta una biblioteca, `ldd -r ./bin/mictlan-ciencia` muestra el nombre. Puedes conservar tus programas en una carpeta separada y retirar el paquete borrando únicamente la copia extraída.

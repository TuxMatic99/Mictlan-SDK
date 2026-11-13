# Mictlán Alpha P0.4

Paquete experimental de consola para Debian 13 de 64 bits en equipos Intel o AMD. Incluye el ejecutor, un ejecutor con funciones científicas, la biblioteca compartida, las cabeceras de Core y las fuentes exactas. El programa se ejecuta desde la carpeta extraída.

## Tu primer programa

En Debian, instala la biblioteca de terminal y el extractor si te hacen falta.

```bash
sudo apt update
sudo apt install libreadline8t64 unzip
unzip mictlan-alpha-p04-linux-x86_64.zip
cd mictlan-alpha-p04-linux-x86_64
sha256sum -c SHA256SUMS
./bin/mictlan ./share/mictlan/ejemplos/hola_mictlan.lat
```

La última línea debe decir `El resultado es: 42`. Guarda estas dos líneas como `primero.mict` con tu editor de texto.

```
nombre = "Mictlán"
escribir("Hola, " .. nombre)
```

Ejecuta `./bin/mictlan primero.mict`. Puedes guardar tus programas en otra carpeta y proporcionar su ruta completa.

## Ciencia y SDK

```bash
./bin/mictlan-ciencia ./share/mictlan/ejemplos/mictlan_ciencia_longitud.mict
./bin/mictlan-ciencia ./share/mictlan/ejemplos/mictlan_suma_vectorial.mict
```

El primer ejemplo devuelve 5. El segundo comienza con las componentes 8 y 16. El ejecutor científico registra `ciencia.longitud2`, `ciencia.producto_punto2` y `ciencia.sumar2`.

Para compilar el SDK completo, extrae `fuentes/SDK.tar.gz`, prepara Raylib 5.5 y pasa a CMake las rutas absolutas a `include`, `lib/liblatino.so` y la instalación de Raylib. Desde esta carpeta puedes usar el siguiente comando, sustituyendo la ruta de Raylib.

```bash
tar -xzf fuentes/SDK.tar.gz
cmake -S Mictlan-SDK -B sdk-build -DCMAKE_BUILD_TYPE=Debug \
  -DLATINO_INCLUDE_DIR="$PWD/include" -DLATINO_LIBRARY="$PWD/lib/liblatino.so" \
  -DCMAKE_PREFIX_PATH=/ruta/a/raylib-instalado
cmake --build sdk-build --parallel 2
ctest --test-dir sdk-build --output-on-failure
```

## Identificación y alcance

Consulta `VERSIONES.txt` para ver las revisiones Git, la plataforma, el compilador y las dependencias. `./bin/mictlan --version` conserva la identificación heredada `Latino 1.5.0`. Si el sistema indica que falta una biblioteca, ejecuta `ldd -r ./bin/mictlan-ciencia` para identificarla.

El paquete prueba consola y ciencia. El SDK completo compila el motor gráfico por separado. En los dos ejecutores se usa el ciclo de vida de P0.2-F de forma predeterminada. La recuperación durante la ejecución se ofrece a anfitriones C mediante `latmemoria.h` y requiere adoptar el contrato descrito en `CONTRATO_MEMORIA.md`. Se conserva la licencia de cada proyecto en `share/doc/mictlan`. Para retirar la copia experimental, conserva tus programas y retira la carpeta extraída.

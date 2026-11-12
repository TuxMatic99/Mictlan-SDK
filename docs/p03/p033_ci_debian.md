# P0.3-3: ejecutar y entender la integración continua

La integración continua repite automáticamente una receta de compilación y pruebas cuando cambia la propuesta del SDK. Cada ejecución identifica exactamente qué Core y qué SDK utilizó; una prueba aprobada con otro ejecutable no acredita esa combinación.

## Qué se ejecuta

El workflow activo es `.github/workflows/p03.yml`. Se dispara al abrir o actualizar una PR hacia `desarrollo/mictlan-alpha`, incluso en borrador. No fusiona, instala ni publica Mictlán. El despacho manual de GitHub solo estará disponible cuando el workflow exista en la rama predeterminada; no es necesario modificar `main` para probar esta PR.

La matriz tiene seis combinaciones: Core P0.2-D y P0.2-E, cada uno en Debug, Release y `sanitizers`. Esta última configuración activa simultáneamente ASan, UBSan y LSan. No se interpreta Debug o Release como comprobación de seguridad de memoria. Los controles independientes comprueban además ASan, UBSan y LSan autónomo por separado.

| Elemento | Revisión fijada |
| --- | --- |
| Core P0.2-D | `e1b3fe6197dfad8c3f8e993b4fdeb79a79a56755` |
| Core P0.2-E, PR #1 en borrador | `ea284f95e46d846771633ecdbcce7f4e61c0b31a` |
| Base SDK | `65c75c8ba1f79c9af91d8634b1edd03bf25f1747` |
| Conservación íntegra de P0.3-1/2 | `1e49c423b9913d4418217987a5ec3eddc0b8921f` |
| Raylib 5.5 | `c1ab645ca298a2801097931d1079b10ff7eb9df8` |

El SDK ejecutado es el SHA exacto de la cabecera de la PR, no un nombre de rama móvil ni el commit de combinación que GitHub genera para revisar PRs. `contrato.json` fija dependencias, cantidad de pruebas, símbolos y disposición de estructuras. Cambiar una revisión exige revisar también esos contratos.

Se conservan las 65 pruebas de verificadores, las 32 funcionales del SDK y las cuatro de recuperación de VM. Se añaden cuatro pruebas reales de integración y nueve del automatizador, además de conservar sus 21 anteriores. Las pruebas reales examinan punteros, valores, contadores de referencias, estado de VM y número de llamadas al destructor; no se limitan a buscar mensajes.

Core se compila completo. Se ejecutan todos sus casos registrados por CTest con el entorno estricto, sin aceptar propiedades que inviertan u omitan fallos. Dos pruebas históricas desactivaban fugas en sus propiedades: se conserva esa evidencia y se ejecuta el mismo comando con detección activada, sin modificar Core. En el perfil instrumentado se ejecutan también sus doce scripts modulares. Los cinco casos de extensiones de archivos se comprueban directamente en todos los perfiles.

Los fallos conocidos se anotan separadamente, pero participan en el resultado global. Un trabajo rojo puede estar comunicando correctamente un defecto ya registrado: no se utiliza `continue-on-error`, `WILL_FAIL`, supresiones o códigos cero de LSan para convertirlo en verde.

## LeakSanitizer en GitHub Actions

Se utiliza `ubuntu-24.04`, una máquina virtual estándar de GitHub, sin `container`, GDB, strace ni envoltorios que tracen los procesos. Esto evita la limitación observada en el entorno local de revisión; su funcionamiento real se comprueba en cada ejecución, no se presupone por el nombre del runner.

El control limpio reserva y libera memoria y debe salir con 0. El control positivo pierde 137 bytes y debe producir un informe real de fuga y terminar con error. Esto se comprueba tanto con LSan integrado como con `-fsanitize=leak`. ASan y UBSan tienen sus propios controles de fallo. Compilar los detectores por separado en estos controles evita que UBSan intercepte primero el fallo destinado a probar ASan; Core y SDK conservan los tres detectores en su configuración instrumentada.

Las opciones estrictas activan fugas, parada ante errores y código 86. Se rechazan opciones que silencien informes, supresiones y `exitcode=0`. El proceso y los compiladores quedan registrados, incluido `TracerPid` cuando Linux lo ofrece. No se cambia la configuración de seguridad del sistema para eludir un bloqueo.

Fuentes primarias consultadas: [LeakSanitizer, LLVM](https://clang.llvm.org/docs/LeakSanitizer.html), [diseño de LSan y uso interno de ptrace](https://github.com/google/sanitizers/wiki/AddressSanitizerLeakSanitizerDesignDocument), [máquinas alojadas por GitHub](https://docs.github.com/en/actions/reference/runners/github-hosted-runners).

## Primer ensayo en Debian, conservando el trabajo existente

Estas órdenes crean copias nuevas. No cambian la rama de los repositorios donde trabajan otros colaboradores. Ejecutar en una terminal normal, sin GDB ni strace.

Primero, instalar las herramientas de compilación si faltan:

```sh
sudo apt-get update
sudo apt-get install build-essential git cmake python3 binutils pkg-config \
  libreadline-dev xorg-dev libgl1-mesa-dev
```

Se requiere CMake/CTest 3.26 o posterior. Debian 13 proporciona una versión suficiente. Después, copiar este bloque; la última orden puede terminar en `FAIL` por los defectos conocidos y conserva el informe:

```sh
(
set -eu
mkdir -p "$HOME/Proyectos/Mictlan"
p033_root=$(mktemp -d "$HOME/Proyectos/Mictlan/p033-revision.XXXXXX")
printf 'Copias e informes: %s\n' "$p033_root"
cd "$p033_root"
git clone --branch verificacion/p03-3-ci --single-branch \
  https://github.com/TuxMatic99/Mictlan-SDK.git SDK
git clone --no-checkout https://github.com/TuxMatic99/Mictlan-Core.git Core
git -C Core checkout --detach ea284f95e46d846771633ecdbcce7f4e61c0b31a
git clone --no-checkout https://github.com/raysan5/raylib.git raylib
git -C raylib checkout --detach c1ab645ca298a2801097931d1079b10ff7eb9df8
p033_sha=$(git -C SDK rev-parse HEAD)
printf 'SDK exacto: %s\n' "$p033_sha"
bash SDK/scripts/p03/preparar_ci.sh debug "$PWD/Core" "$PWD/raylib" \
  "$PWD/resultados-debug" "$p033_sha" p02e
)
```

`checkout --detach` solo sitúa la copia nueva en una revisión fija; no modifica ninguna rama existente. Dentro de la carpeta mostrada, repetir la última orden cambiando `debug` por `release` o `sanitizers` y usando un directorio nuevo, por ejemplo `resultados-release` o `resultados-sanitizers`. El script se niega a sobrescribir resultados anteriores.

Para comparar P0.2-D, crear otra copia de Core y situarla en su SHA de la tabla; usar `p02d` como último argumento y otro directorio de resultados. No es necesario combinar ramas.

## Cómo leer los resultados

| Resultado | Significado |
| --- | --- |
| `PASS` | Terminó la comprobación correspondiente sin fallos observados. |
| `FAIL` | Falló el programa, un contrato, una prueba, la preparación o un detector. Los detalles conservan subtipos como `FAIL_SANITIZER` o `INVALID_CONFIG`. |
| `BLOCKED_INFRASTRUCTURE` | No se pudo terminar una comprobación por una restricción demostrada del entorno. No es una aprobación. |

Códigos del automatizador: 0 aprobado; 1 fallo; 2 bloqueo; 3 configuración inválida. Si hay a la vez un fallo demostrado y un bloqueo, prevalece el fallo y se conservan ambas trazas. En JUnit, un bloqueo se registra como error, nunca como prueba omitida/aprobada.

Abrir `resultados-.../evidence/report.json` para el resumen por componente y los SHA. Los archivos `.stdout.log` y `.stderr.log` contienen las salidas completas; los `.xml` son informes JUnit. `preparation.log` y `preparation.json` explican problemas de compilación. En GitHub, abrir la ejecución de Actions y descargar su artefacto, incluso cuando el trabajo haya fallado. Los artefactos se retienen 14 días.

Las dependencias de sistema se registran mediante `packages.txt`; las revisiones Git sí están fijadas. Los paquetes de Ubuntu/Debian y la imagen del runner pueden actualizarse: esto ofrece trazabilidad, no una compilación bit a bit de todo el sistema operativo. En un Core privado haría falta un token de lectura autorizado; la ausencia de acceso produce bloqueo de preparación, no éxito.

La biblioteca de Raylib no se instrumenta en este frente; sí Core, SDK y sus ejecutables de integración. No se certifican GPU, otros sistemas operativos, otras arquitecturas ni todos los contratos de propiedad existentes.

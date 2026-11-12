# P0.3-1: errores esperados y sanitizadores

Los tests `mictlan_ciencia_suma_error_tipo` y `mictlan_ciencia_suma_error_rango`
solo aceptan el retorno 1 si aparece su diagnostico de lenguaje, stdout contiene
el encabezado esperado y no hay informes de sanitizadores en ninguno de los dos
streams. El helper comun esta en `tests/p03/verificar_error_esperado.cmake`.

Un error fatal de LeakSanitizer, incluido el impedimento por `ptrace`, se marca
`BLOCKED_INFRASTRUCTURE`. Su retorno es no nulo: nunca cuenta como prueba
aprobada. Si ademas hay un UAF o un informe UBSan, se conserva ese fallo de memoria
como clasificacion principal y el bloqueo permanece en la traza.

## Verificar los propios verificadores

Requisitos de esta guia: Linux/POSIX, Python 3.8 o posterior y CMake/CTest 3.26 o
posterior. El helper conserva compatibilidad con CMake 3.18 del SDK; las opciones
JUnit y `--no-tests=error` de los comandos siguientes requieren herramientas mas
recientes. No se validaron Windows ni macOS.

Desde el directorio que contiene `mictlan-sdk`:

```bash
cmake -S mictlan-sdk/tests/p03 -B build-p03-verificadores
ctest --test-dir build-p03-verificadores \
  --output-on-failure --no-tests=error \
  --output-junit p03-verificadores.xml
```

Esta bateria independiente tiene 56 casos de verificadores y 9 del control
previo de LSan. No necesita compilar Core, SDK ni Raylib. Las salidas de
sanitizadores son simuladas: sus 65 aprobaciones prueban la clasificacion del
verificador, no la seguridad de memoria del lenguaje.

Se incluyen controles limpios; informes ASan, UBSan y LSan en stdout/stderr;
UBSan sin nombre del motor; senales; timeout; diagnostico ausente; retorno
incorrecto; archivos ausentes; opciones que desactivan detectores; redireccion
de logs; supresiones y bloqueo de infraestructura. Los casos negativos requieren
que falle el wrapper con la clasificacion correcta; no se utiliza `WILL_FAIL`.

Las opciones invalidas, incluido `LSAN_OPTIONS=exitcode=0`, solo se suministran
en fixtures para demostrar que se rechazan antes de ejecutar la entrada simulada.
No se usan para aprobar comprobaciones reales.

## Comprobacion directa de tipo y rango

El automatizador lee las fuentes y los builds existentes. **No recompila ni
modifica Core**, no cambia ramas y no crea commits. Antes de ejecutarlo, el
responsable de P0.2 debe haber construido su biblioteca y reconstruido el SDK
contra ella. Las rutas se validan; los hashes identifican los binarios realmente
probados. La coincidencia de rutas por si sola no acredita la frescura del build.

```bash
python3 mictlan-sdk/scripts/p03/verificar_errores.py \
  --sdk-build build-sdk-asan \
  --core-source mictlan-core \
  --core-build build-core-asan \
  --profile sanitizers \
  --output artefactos/p03/p03-1-asan-01
```

`--output` debe ser un directorio nuevo fuera de los repositorios. Usar otro
nombre para la siguiente ejecucion: el programa rechaza sobrescribir evidencias.
Puede indicarse `--cmake /ruta/cmake` si la herramienta no esta en PATH.

El perfil instrumentado exige simbolos de instrumentacion ASan/UBSan en el
ejecutor y la biblioteca Core, y comprueba la ruta resuelta de `liblatino.so`.
Luego compila un control independiente, con el compilador registrado en el
Core: uno libera una reserva y otro deja intencionalmente 137 bytes pendientes.
La precondicion solo pasa si el primero termina limpio y el segundo detecta
esa fuga. No se cuentan estos controles como pruebas de la VM.

Las opciones efectivas incluyen:

```text
ASAN_OPTIONS=detect_leaks=1:halt_on_error=1:detect_stack_use_after_return=1:exitcode=86
UBSAN_OPTIONS=halt_on_error=1:print_stacktrace=1:exitcode=86
LSAN_OPTIONS=leak_check_at_exit=1:exitcode=86
```

Se conservan opciones adicionales del entorno, pero se rechazan opciones
identificadas que debiliten estos controles, redirijan los informes fuera de
stdout/stderr o introduzcan supresiones. El retorno 86 no identifica por si solo
el motor que fallo: siempre se conservan e inspeccionan los diagnosticos.

Aunque falle el control LSan, se ejecutan tipo/rango como diagnosticos y se
guardan sus salidas. El resultado global permanece bloqueado o fallido. Una
ejecucion no puede aprobar si cambiaron fuentes, cabeceras, caches o binarios
durante la comprobacion.

Para funcionamiento sin instrumentacion:

```bash
python3 mictlan-sdk/scripts/p03/verificar_errores.py \
  --sdk-build build-sdk-debug \
  --core-source mictlan-core \
  --core-build build-core-debug \
  --profile debug \
  --output artefactos/p03/p03-1-debug-01
```

## Resultados y trazabilidad

| Retorno del automatizador | Estado | Significado |
|---|---|---|
| 0 | `PASS_FUNCTIONAL` | Solo comportamiento Debug de tipo/rango |
| 0 | `PASS_SANITIZERS` | Esos dos casos y control LSan aprobados en el perfil instrumentado |
| 1 | `FAIL` | Error real, oraculo incumplido o control previo incorrecto |
| 2 | `BLOCKED_INFRASTRUCTURE` | LSan no pudo completar su comprobacion |
| 3 | `INVALID_CONFIG` | Parametros, builds o entorno no validos |

Un error de argumentos anterior a la creacion de `--output` retorna 3 sin crear
informe. Si el directorio se pudo crear, se escriben `report.json` y `report.md`,
incluido el motivo de una configuracion rechazada.

`report.json` registra los SHAs, ramas, estado Git, hash del diff y de archivos
nuevos, cabeceras, binarios, caches, opciones, compilador, plataforma, comandos,
retornos y duraciones. Las fechas del registro automatico se expresan en UTC.
Los informes humanos de coordinacion pueden usar America/Mexico_City.

Cada caso conserva `tipo/` o `rango/` con `stdout.log`, `stderr.log`, `estado.txt`
y `clasificacion.txt`. Tambien se guardan las salidas completas de CMake y de los
controles. `MICTLAN_LOG_DIR` permite usar esta misma conservacion al invocar los
wrappers CMake directamente; cada llamada concurrente debe usar un directorio
distinto. Sin ese parametro, los fallos muestran ambos streams en CTest.

El automatizador no ejecuta las 32 pruebas del SDK ni acredita su ABI completa.
La suite existente se sigue ejecutando por separado:

```bash
ctest --test-dir build-sdk-debug --output-on-failure --no-tests=error
```

No interpretar un total de pruebas seleccionadas como prueba de que tipo/rango
quedaron libres de informes sanitizados. Revisar sus nombres, configuracion,
streams y resultado individual.

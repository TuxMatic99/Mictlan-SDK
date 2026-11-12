# P0.3-2: recuperacion de VM y propuesta de CI

Fecha de referencia: 2026-11-11, Mexico. Ejecuciones registradas tambien en UTC
(2026-11-12). Rama local: `verificacion/p03-work`, base SDK
`65c75c8ba1f79c9af91d8634b1edd03bf25f1747`. Sin commits ni publicaciones.

## Alcance y conservacion

Los diez archivos de P0.3-1 permanecen byte por byte sin cambios. Se preservaron
en un parche independiente, SHA-256
`e33da07efa15087c4e9dd02e5d9f46fa6722fc54e7224d35827d15f7b5ab2354`.
El parche se aplico realmente, ademas de `git apply --check`, sobre una copia
limpia y aislada de SDK `65c75c8`; los diez archivos resultantes coinciden.
No se edito codigo de Core, sus cabeceras, la rama de P0.2 ni el CMake principal
del SDK. Se compilo una copia aislada del nuevo commit publicado por P0.2,
en HEAD separado y con builds fuera de las fuentes; su arbol permanecio limpio.
Las 65 pruebas de verificadores y las 32 funcionales siguen separadas.

## Regresion real de la VM

`tests/p03_vm` es un proyecto CMake independiente que enlaza la biblioteca real
`liblatino.so` y los fuentes existentes del puente cientifico del SDK. No
incluye archivos `.c` de Core ni reemplaza sus funciones por simulaciones.
Cada proceso crea una sola VM y reutiliza los programas compilados.

| Modo | Comprobacion |
|---|---|
| `control` | Funciones anidadas y FFI `ciencia.longitud2(3,4)`, retorno 5, sin errores provocados. |
| `directa` | Error de tipo, llamada valida, error de rango, llamada valida, errores consecutivos y mas llamadas validas. |
| `anidada` | Misma secuencia atravesando dos funciones Mictlan antes de entrar en FFI. |
| `pila` | Tipo incorrecto en el ultimo argumento; el fallo ocurre cuando aun quedan tres argumentos por retirar. |

Se exigen `LAT_ERRRUN == 2` (tambien al compilar), estado interno 2 para errores
y 0 para llamadas correctas. El codigo 1 de la consola es otra interfaz.
La prueba compara `ptrctx`, `contexto_actual`, contexto global, `numejec`,
`ptrpila`, coherencia `tope/pila`, manejador `error`, identidad de VM/global y
estado de bucle/clase. Registra `ptrprevio` y `prev_args` y comprueba sus rangos;
no exige que sean identicos entre llamadas correctas porque Core los utiliza
para comunicar argumentos y retornos. No lee `base`, `actfun` o `status`, que
no se inicializan de forma suficiente en la base revisada para este contrato.
La memoria utilizada no se exige constante: las tablas de la VM pueden crecer.

La unica retirada de pila hecha por la prueba consume el retorno esperado de
una llamada correcta. Nunca restablece contadores o contextos manualmente.
Emite una linea JSON por llamada y un resumen al terminar los destructores.
Un resumen funcional correcto no anula un informe posterior de LSan al salir.

CTest solicita 200 ciclos. El ejecutable permite de 1 a 1000; cada ciclo con
errores contiene seis errores y cuatro llamadas validas. Antes de cada llamada
comprueba que sea seguro continuar. Se detiene con fallo si encuentra pila
incoherente/no recuperada, `ptrctx >= 32` o `numejec >= 128`, dejando margen
respecto de los limites de Core. No puede declarar 200 ciclos aprobados si se
detuvo antes. No usa `WILL_FAIL`, saltos ni inversion del resultado.

### Ejecucion independiente junto al Core local de P0.2

Usar una biblioteca y sus cabeceras correspondientes, ya compiladas por P0.2.
Estas ordenes solo compilan fuentes de pruebas/SDK en un directorio nuevo.
Sustituir las tres rutas de ejemplo por las reales; no copiar literalmente.

```bash
cmake -S /ruta/mictlan-sdk/tests/p03_vm -B /ruta/build-p03-vm-debug \
  -DCMAKE_BUILD_TYPE=Debug \
  -DLATINO_INCLUDE_DIR=/ruta/mictlan-core/include \
  -DLATINO_LIBRARY=/ruta/build-core-debug/liblatino.so
cmake --build /ruta/build-p03-vm-debug --parallel 2
ctest --test-dir /ruta/build-p03-vm-debug --no-tests=error -V \
  --output-junit /ruta/p03-vm-debug.xml
```

Para probar 1000 ciclos: `build-p03-vm-debug/p03_vm_recuperacion directa 1000`.
El limite no obliga a completar ciclos cuando ya se detecto un estado inseguro.
Para sanitizadores usar OTRO directorio y la biblioteca Core instrumentada,
anadiendo `-DCMAKE_C_FLAGS="-g -O0 -fsanitize=address,undefined
-fno-sanitize-recover=all -fno-omit-frame-pointer"` y
`-DCMAKE_EXE_LINKER_FLAGS=-fsanitize=address,undefined` al configurar.
Mantener deteccion de fugas, errores fatales y salidas no nulas; el automatizador
completo establece opciones estrictas y rechaza opciones que oculten fallos.

## Comparacion de las dos revisiones de Core

Core: `e23a134b199687399f28840c73bfe7b8073cf444`, anterior a P0.2-A/B.
Entorno: Debian 13 x86_64, GCC 14.2.0, CMake/CTest 3.31.10.

| Comprobacion | Resultado observado |
|---|---|
| Verificadores P0.3-1 | 65/65 aprobados, simulaciones de informes y preflight. |
| SDK Debug | 32/32 aprobados, incluida comprobacion directa de tipo/rango. |
| Clasificador nuevo de CI | 21/21 aprobados, pruebas simuladas adicionales. |
| VM control | 200/200 ciclos; tambien 1000/1000 en ejecucion separada. |
| VM directa | Fallo: primer error deja `ptrctx=1`, `numejec=1`, `ptrpila=0`; parada preventiva durante ciclo 6. |
| VM anidada | Fallo: primer error deja `ptrctx=3`, `numejec=3`, `ptrpila=0`; parada durante ciclo 2. |
| VM pila | Fallo: primer error deja `ptrpila=3`, `ptrctx=1`, `numejec=1`; parada antes de la llamada siguiente. |
| Controles positivos ASan/UBSan | Detectaron realmente desbordamiento de buffer y de entero; salida 86. Son defectos intencionales de los controles. |
| LSan, incluso control limpio independiente | Bloqueado por `ptrace`. No acredita ausencia ni cantidad de fugas. |
| SDK con sanitizadores | 32 casos bloqueados por LSan en este entorno; ninguno certificado como aprobado. |

Las llamadas validas observadas despues de errores retornaron 5 con estado 0,
pero no repararon los contadores. El fallo de recuperacion domina el resultado
global, aun cuando tambien exista bloqueo de infraestructura. Los resultados
9/9 Core ASan, 30/30 SDK ASan seleccionados y 32/32 SDK Debug de P0.2 son informes
del usuario; no se confunden con nuestras comprobaciones.

Durante esta etapa aparecio en GitHub el commit
`0b4f8df58935e425640824406406d95c9dc3281f`, hijo directo de e23a134, publicado
por P0.2 con la recuperacion de contextos, descriptor local y restauracion de
`numejec`. Se descargo en otra copia, se compilaron Core, SDK y regresion desde
cero en Debug y con sanitizadores, y se repitieron las comprobaciones reales.

| Prueba sobre 0b4f8df | Resultado observado |
|---|---|
| SDK Debug | 32/32 aprobados. |
| VM control/directa/anidada | Cada caso completa 200 ciclos Debug sin fallos. |
| Stress directa y anidada | Cada modo completa 1000 ciclos: 6000 errores internos 2 y 4000 llamadas validas 0, mas una llamada de definiciones; `ptrctx`, `numejec` y `ptrpila` vuelven a 0. |
| VM pila | Sigue fallando: el tipo incorrecto en el ultimo argumento deja `ptrpila=3`; `ptrctx` y `numejec` SI vuelven a 0. |
| Tipo/rango y VM con sanitizadores | Sin aprobacion sanitaria: LSan bloqueado por ptrace. El fallo funcional de pila permanece visible y tiene prioridad sobre ese bloqueo. |
| ABI examinada | Layout identico; se agrega `latMV_recuperar_contextos`, sin retirar exportaciones. Las 25 importaciones lat* examinadas se resuelven. |

Esta evidencia confirma recuperacion funcional de `numejec` en las secuencias
ensayadas. No cierra fugas, seguridad de todas las clases/constructores ni toda
la recuperacion de VM: la pila sigue pendiente. Los fallos de e23a134 se
conservan como comparacion, no se atribuyen al commit nuevo.

## Contrato entre Core y SDK

`ci/p03/contrato.json` fija el SHA de Core y la base aprobada del SDK. El SHA del
SDK que se ejecutara en CI es el SHA completo del evento, no un nombre de rama.
La propuesta se fija ahora en Core `0b4f8df`, verificado durante esta etapa;
`baseline_core_sha` conserva e23a134 como referencia. No se ha publicado ese cambio.
Se exige que descienda de la base y que ambos repositorios esten limpios.
Para revision local se permite explicitamente un SDK modificado mediante
`--allow-sdk-dirty`; se etiqueta `WORKTREE_REVIEW` y conserva hashes del diff y
de archivos nuevos. Esto no equivale a un nuevo commit identificado solo por 65c75c8.

Se revisan cabeceras y rutas de CMake, hashes de bibliotecas y consumidores,
exportaciones `lat*`, importaciones del SDK y resolucion real con `ldd -r`.
La huella publica Linux x86_64 registra `sizeof(lat_mv)=5688`,
`sizeof(lat_objeto)=64`, `LAT_ERRRUN=2` y offsets de campos sensibles.
No es una certificacion exhaustiva de ABI ni sustituye `abidiff`: un simbolo
con el mismo nombre puede cambiar de firma, estructura o comportamiento.
Una modificacion de cabeceras requiere reconstruir los consumidores y revisar
el contrato, no solo sustituir `liblatino.so`.

El ejecutor local recibe builds existentes, identifica sus rutas y hashes y
comprueba que no cambien durante la corrida. No puede probar por si solo que
un build antiguo se reconstruyo despues de cada cambio de fuente. La propuesta
CI elimina esa ambiguedad compilando copias limpias en directorios nuevos.

## Automatizacion preparada, sin activar

`ci/p03/github-actions.yml` es una plantilla fuera de `.github/workflows`.
No se ha enviado a GitHub ni ejecutado en sus servidores. Fue analizada como
YAML y sus bloques shell pasaron `bash -n`; no se dispone de `actionlint`.
Las acciones y Raylib se fijan a SHAs consultados en GitHub, no a etiquetas
moviles. El primer runner propuesto es Ubuntu 24.04 para una comprobacion
Linux estandar; Debian 13 se ha probado localmente. No afirmar equivalencia
total de ambos entornos. Una matriz Debian debe incorporarse como etapa posterior.

Flujo preparado:

1. Descargar SDK en SHA del evento, Core en SHA de contrato y Raylib 5.5 en SHA
   `c1ab645ca298a2801097931d1079b10ff7eb9df8`.
2. Instalar dependencias del runner y registrar versiones de paquetes.
   Los paquetes apt no estan fijados a un snapshot; la reproducibilidad aun
   no es bit por bit.
3. Compilar Raylib, Core, SDK y regresion en directorios nuevos separados.
   Hay dos trabajos: Debug y Debug con ASan/UBSan/LSan, sin cancelar el otro
   al encontrar un fallo.
4. Revisar contrato, instrumentacion ASan/UBSan en biblioteca/ejecutor/regresion,
   ejecutar controles positivos independientes y control limpio/positivo LSan.
5. Ejecutar 65 verificadores, 32 pruebas SDK y 4 pruebas VM. Los 21 casos del
   clasificador se ejecutan antes. No se excluyen fallos conocidos.
6. Conservar salida completa, comandos, versiones, hashes, inventario CTest,
   JSON y JUnit incluso si la bateria falla. Un bloqueo produce resultado no
   aprobado, con categoria propia; no se presenta como prueba omitida aprobada.

El archivo JSON de fallos conocidos es informativo: no cambia los retornos.
`ejecutar_bateria.py` devuelve 0 solo si todo lo exigido pasa, 1 ante fallos,
2 ante bloqueo de infraestructura sin fallos reales adicionales y 3 ante
configuracion invalida. Un XML ausente, vacio, duplicado o con pruebas omitidas
es fallo. Un informe sanitario con salida cero tambien es fallo.
Se amplia a 16 MiB el limite de salida por prueba en JUnit y se rechaza cualquier
aviso de recorte. La salida completa de CTest se conserva ademas en archivos de
texto: el limite predeterminado recortaba el caso VM aprobado a 1024 bytes.

Para usar el ejecutor local, tras configurar los cuatro builds:

```bash
python3 scripts/p03/ejecutar_bateria.py \
  --sdk-build /ruta/build-sdk-debug \
  --core-source /ruta/core-publicado-limpio \
  --core-build /ruta/build-core-debug \
  --vm-build /ruta/build-p03-vm-debug \
  --verifiers-build /ruta/build-p03-verificadores \
  --profile debug --expected-sdk-sha 65c75c8ba1f79c9af91d8634b1edd03bf25f1747 \
  --allow-sdk-dirty --output /ruta/informe-nuevo
```

El contrato completo exige el Core publicado fijado. Para los cambios locales
no publicados de P0.2, ejecutar primero la regresion independiente; no editar
ni hacer limpio forzosamente el arbol de P0.2 para satisfacer CI.

## Integracion incremental propuesta

Primero revisar los dos parches: P0.3-1 congelado y P0.3-2 adicional. Solo con
autorizacion crear los commits del SDK. P0.2 conserva la propiedad de Core.
Entregarle la regresion para que la ejecute sobre su build actualizado y
conserve el SHA, diff local y trazas de las cuatro pruebas. Exigir 200 ciclos
completos por caso y, despues, 1000 ciclos con errores en una VM ya recuperable.
Directa y anidada ya satisfacen ambos niveles en 0b4f8df; falta el caso pila.

Cuando P0.2 corrija la recuperacion de pila, actualizar de nuevo el SHA de contrato
en un cambio separado del SDK, revisar su ABI y reconstruir ambos lados.
Repetir tipo/rango directamente y la matriz completa en Debian sin `ptrace`.
No basta una simulacion de los verificadores para cerrar una correccion de Core.

Tras la autorizacion de publicacion, llevar la plantilla al directorio de
workflows y resolver su presencia inicial en la rama predeterminada: GitHub
requiere eso para ofrecer `workflow_dispatch`. La rama `main` del SDK no
coincide con nuestra base de trabajo; no fusionarla automaticamente.
Si Core es privado, configurar antes una credencial de solo lectura autorizada
para ese repositorio; el token ordinario del SDK no concede acceso a otro
repositorio privado. Despues de una corrida manual revisada, proponer el evento
`pull_request` y los controles obligatorios. No habilitar aprobaciones verdes
parciales mientras los trabajos de recuperacion o memoria sigan fallando.

Fuentes: documentacion oficial de CTest (`--output-junit`, `--no-tests=error`),
GitHub Actions (`workflow_dispatch`) y README de `actions/checkout` en el SHA
fijado. Los resultados propios se sustentan en JSON/JUnit y trazas entregados.

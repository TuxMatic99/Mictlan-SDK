# P0.3-3 — Auditoría y coordinación

Referencia: 11 de noviembre de 2026, México; ejecuciones locales: 12 de noviembre UTC. La entrega final identifica el commit SDK y enlaza las ejecuciones reales de GitHub Actions.

## Conservación y límites

Los veinte archivos de P0.3-1/2 se recuperaron del parche completo, SHA-256 `71d0fd39a7c6078f0cc653a336fa445b4f254af7ad1dd80e1fa1fae282b80545`. Se verificó su aplicación sobre SDK `65c75c8ba1f79c9af91d8634b1edd03bf25f1747` y su igualdad byte por byte con la copia local anterior. Se conservaron en el commit separado `1e49c423b9913d4418217987a5ec3eddc0b8921f`, antes de modificarlos. La propuesta histórica `ci/p03/github-actions.yml` permanece como documento de P0.3-2; el workflow activo es `.github/workflows/p03.yml`.

Antes de editar se inspeccionaron los archivos publicados por GitHub en sus SHA exactos. Los archivos que todavía no existían remotamente se conservaron primero en el commit anterior; se contrastaron de nuevo contra su contenido remoto antes de ampliarlos. No se modificaron fuentes de Core, las ramas originales ni el frente P0.2-D2.

## Auditoría de la PR #1

P0.2-D (`e1b3fe6`) y P0.2-E (`ea284f9`) son commits hermanos sobre `0b4f8df`. D solo añade el registro CMake y la prueba de dos contenedores. E cambia 17 líneas de `src/latdo.c`, además de su prueba, registro e informe. No difieren sus cabeceras ni otros archivos de implementación.

La corrección de E mantiene las recuperaciones de contexto y `numejec`, limita la pila al entrar en cada manejador y restaura `ptrprevio`/`prev_args`. No destruye celdas prestadas, no altera las estructuras públicas y no vuelve a introducir argumentos consumidos. Esa frontera es coherente con las operaciones de apilar/desapilar de esta base. No equivale a deshacer cambios en objetos o variables.

El parche completo de E pasa `git apply --cached --check` sobre D en un índice temporal. Es una comprobación de aplicación, **no una fusión ni una ejecución de un Core combinado**. Se compilan y prueban D y E por separado. No se cambia la PR #1 ni su condición de borrador.

El contrato binario se comprueba por símbolos exportados, importaciones del SDK, carga de la biblioteca correcta y disposición de estructuras en Debian x86_64. Se mantienen 278 símbolos definidos en las compilaciones funcionales y se resuelven las 37 importaciones `lat*` distintas del SDK y las nuevas pruebas. No es una certificación ABI completa de todas las extensiones o arquitecturas.

## Resultado local antes/después

Entorno local: Debian 13, GCC 14.2.0 y CMake/CTest 3.31.10. Se compilaron las seis combinaciones por separado. La copia SDK tenía los cambios de P0.3-3 pendientes, identificados mediante hashes y `WORKTREE_REVIEW`; las ejecuciones de GitHub comprobarán el commit publicado limpio.

| Comprobación | Core P0.2-D | Core P0.2-E |
| --- | --- | --- |
| SDK Debug y Release | 32/32 en cada perfil | 32/32 en cada perfil |
| Recuperación de VM, Debug y Release | 3/4; sigue fallando la pila | 4/4 |
| Nuevos contratos de integración, Debug y Release | 4/4 | 4/4 |
| Core CTest Debug y Release | 1/2; falla `coverage` | 10/11; falla `coverage` |
| Verificadores simulados conservados | 65/65 | 65/65 |
| Clasificadores anteriores | 21/21 | 21/21 |
| Nuevas regresiones del automatizador | 9/9 | 9/9 |

Esta tabla conserva la primera validación local. Después se añadieron otras dos
regresiones del clasificador (11/11) al revisar las salidas reales de GitHub.

Los cuatro contratos nuevos comprueban identidad, elementos repetidos gestionados mediante recursos, reemplazos y alias de listas producidas por la FFI real. Los tres casos de recursos repiten 200 ciclos y verifican referencias, destrucciones y saldo interno de memoria. El caso FFI comprueba valores y la persistencia del alias después de una reasignación. Cierra la VM normalmente, sin introducir liberaciones manuales destinadas a ocultar fugas.

En este entorno local, los controles LSan limpio y con fuga, tanto integrados como autónomos, están bloqueados por `ptrace`. Por tanto, las pruebas instrumentadas afectadas no se consideran aprobadas. ASan y UBSan sí detectan sus controles positivos. Los dos UAF conocidos de listas anidadas y elementos repetidos permanecen visibles. `coverage` es un fallo de configuración, incluso cuando LSan impide vaciar el mensaje de stdout.

Se detectaron y corrigieron dos problemas en la automatización: la clasificación que podía ocultar el fallo de `coverage` bajo un bloqueo LSan y la resolución de `..` a través de un enlace simbólico que podía elegir un ejecutable Debug vecino. La prueba de extensiones ahora copia únicamente el script histórico sin cambiar sus bytes a un directorio temporal real y registra el hash del ejecutable seleccionado. Las salidas originales y la repetición corregida se conservan en evidencias.

Raylib desde fuentes no se pudo configurar localmente por falta de cabeceras X11. La matriz local utilizó la biblioteca Raylib 5.5 previamente disponible, con sus rutas registradas. El workflow instala las dependencias gráficas de desarrollo y compila el SHA fijado desde fuentes. No se presenta la ejecución local como prueba de esa fase de preparación de GitHub.

## Primera ejecución real de GitHub Actions

La ejecución [43158783575](https://github.com/TuxMatic99/Mictlan-SDK/actions/runs/43158783575)
compiló las seis combinaciones desde fuentes, incluido Raylib, con SDK
`4f1c7ad980c46473a034c9b9f303ec2811247067`, Ubuntu 24.04 y GCC 13.3.0.
Los controles de ASan, UBSan y LSan (integrado y autónomo) pasaron en D y E.
No hubo bloqueo de LSan. Las pruebas directas de tipo y rango pasaron sin
informes de sanitizadores. El SDK pasó 32/32 en Debug y Release, y 30/32 con
sanitizadores: suma vectorial fugó 600 bytes y alias FFI, 528 bytes.
Los tres contratos de recursos pasaron; el nuevo caso de alias FFI expuso
otros 528 bytes en su ejecución independiente. Core mantuvo la fuga de
528 bytes, los dos UAF conocidos y el fallo de configuración `coverage`.
La VM pasó 4/4 con E en los tres perfiles; con D falló la recuperación de
los tres argumentos. Los doce scripts modulares pasaron con sanitizadores.

La revisión de las trazas también identificó tres falsos positivos del
clasificador: confundía la ruta `p03-p02e-sanitizers` mostrada por los errores
esperados de extensión con un informe de sanitizador. Se corrigió el
reconocimiento de diagnósticos y se añadieron pruebas para rutas legítimas y
salidas contaminadas. Los registros de esta primera ejecución permanecen
intactos; la entrega final enlaza la repetición del commit corregido. Esta
corrección no modifica ni oculta las fugas o los UAF anteriores.

## Fallos y trabajo separado

| Situación | Clasificación y siguiente paso |
| --- | --- |
| UAF en listas anidadas y elementos repetidos | Alta gravedad; responsabilidad del frente de propiedad P0.2-D2. No se tocan destructores. |
| Recuperación de pila en D | Defecto reproducido; E lo corrige funcionalmente. Mantener visible la comparación. |
| Fugas de las listas FFI y otras rutas | Confirmadas por LSan en GitHub: 600 bytes en suma vectorial y 528 en alias; coordinar con P0.2-D2. |
| `coverage` apunta a un programa ausente | Fallo de configuración heredado, conservado sin modificar Core. |
| Constructores y propiedad general de temporales | Fuera de la cobertura de esta entrega; no deducir seguridad global de las pruebas aprobadas. |
| Bloqueo LSan local | `BLOCKED_INFRASTRUCTURE`; requiere un entorno donde el control limpio y el positivo puedan completarse. |

P0.3-3 → P0.2/P0.2-D2: se conservan y automatizan los contratos sin modificar la propiedad de objetos. La PR #1 permanece separada; la compatibilidad con D se evalúa sin fusionar. El resultado global de CI debe seguir siendo fallo mientras existan defectos reales, aunque las pruebas funcionales del SDK pasen. Revisar los informes de fugas obtenidos en GitHub y coordinar su resolución antes de aprobar una integración.

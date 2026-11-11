# Informe de avance 03 | Mictlán sale del laboratorio: primera distribución verificable

| Campo | Detalle |
|---|---|
| Proyecto | Mictlán, lenguaje y ecosistema de programación de propósito general |
| Fecha de corte | 6 de noviembre de 2026 |
| Hito | Primera distribución de consola portable, documentada, empaquetada y validada mediante un script |
| Estado | Hito experimental logrado; alfa pública Debian todavía pendiente |
| Alcance del informe | Evidencias de terminales, informes 01 y 02, y documentación técnica oficial |
| Meta de referencia | Alfa pública experimental para Debian x86_64, con fecha tentativa del 2 de diciembre de 2026 (según el informe 01) |

> **Criterio de rigor:** «Compila», «pasa las pruebas», «se ejecuta en esta computadora» y «se puede instalar en otra computadora» son afirmaciones diferentes. Este informe solo da por verificadas las tres primeras cuando existen resultados; la compatibilidad en otros equipos sigue pendiente.

## 1. Resumen ejecutivo

Mictlán parte de Latino y se desarrolla como lenguaje de propósito general con sintaxis en español. El proyecto ya está dividido en tres repositorios locales: **mictlan-core**, **mictlan-sdk** y **mictlan-lab**. Se conservaron sus responsabilidades independientes para evitar que el núcleo se mezcle con la lógica de interfaz de usuario o con una aplicación de demostración.

El informe 01 documentó la biblioteca de círculos 2D todavía sin renderizado. El informe 02 documentó el primer círculo visible desde un archivo `.lat`, con botones y eventos funcionales. Desde entonces se completaron dos avances adicionales: **una FFI gráfica separada de `host_ui.c`, con 25 pruebas automatizadas aprobadas**, y **una distribución mínima del intérprete, generada y verificada automáticamente**.

El script `mictlan-core/scripts/empaquetar_portable.sh` configura Release, compila, instala el componente `MictlanPortable`, crea un `.tar.gz`, comprueba SHA-256, extrae el paquete y ejecuta `hola_mictlan.lat`. Su última ejecución terminó satisfactoriamente con un archivo comprimido de **96K**, según `du -sh`, y el resultado esperado **42**.

**Conclusión:** el prototipo de consola es distribuible de forma experimental en el entorno Linux probado, pero **no está listo todavía para una publicación pública responsable**: faltan la revisión integral de licencias y atribuciones, el ajuste de la identidad y versión de CPack, las dependencias del `.deb`, pruebas en un sistema limpio y documentación de soporte. La aplicación gráfica continúa funcional en el entorno de desarrollo, pero aún no tiene su propia distribución instalable.

## 2. Evolución respecto a los informes anteriores

| Hito | Situación al registrarse | Evidencia posterior | Estado al corte |
|---|---|---|---|
| 01. El lienzo toma forma | Biblioteca `mictlan_dibujo2d`; 24/24 pruebas; sin renderizar el círculo | Renderizador Raylib y FFI incorporados | Superado |
| 02. Del lenguaje al píxel | Círculo visible desde `.lat`; 24/24 pruebas; FFI aún dentro del host | Nueva prueba FFI y extracción a módulo independiente | Superado |
| 03. Mictlán sale del laboratorio | No existía una distribución portable automatizada y documentada | Instalación aislada, script de empaquetado, extracción y SHA-256 | Logrado experimentalmente |

**Nota:** las limitaciones escritas en los informes 01 y 02 describían correctamente su momento histórico. No deben confundirse con el estado actual.

## 3. Arquitectura de tres repositorios

```text
~/Proyectos/Mictlan/
├── mictlan-core/                  Intérprete y base del lenguaje
│   ├── ejemplos/hola_mictlan.lat
│   ├── docs/README_PORTABLE.md
│   ├── scripts/empaquetar_portable.sh
│   └── src/CMakeLists.txt
├── mictlan-sdk/                   UI, gráficos, FFI y pruebas
│   ├── include/mictlan_dibujo2d.h
│   ├── include/mictlan_render_raylib.h
│   ├── include/mictlan_graficos_ffi.h
│   ├── src/graficos/dibujo2d.c
│   ├── src/graficos/dibujo2d_raylib.c
│   ├── src/graficos/mictlan_graficos_ffi.c
│   ├── src/ui/host_ui.c
│   ├── tests/datos/mictlan_graficos_ffi.lat
│   └── docs/informes/
├── mictlan-lab/                   Aplicación de referencia
│   └── aplicacion/prueba_circulo.lat
├── build-core-debug/             Compilación de desarrollo, fuera de Git
├── build-core-release/           Compilación optimizada, fuera de Git
├── build-sdk-debug/              SDK de pruebas, fuera de Git
└── artefactos/                   Paquetes generados, fuera de los tres repositorios
```

Esta representación recoge los archivos y carpetas que constan en las salidas y explicaciones anteriores; **no es una auditoría completa del árbol de directorios**.

**Separación acordada:** Core proporciona el lenguaje; SDK implementa capacidades gráficas y de integración; Lab las consume para detectar necesidades reales. Mictlán Core no debe depender de Mictlán Lab ni incorporar código específico de una demostración.

### Flujo de ejecución gráfica comprobado

```text
Archivo .lat de Mictlán Lab
          ↓
Intérprete y registro FFI `graficos.circulo()`
          ↓
`mictlan_graficos_ffi.c`
          ↓
`dibujo2d.c` (validación y almacenamiento)
          ↓
`dibujo2d_raylib.c` (renderización)
          ↓
Raylib / OpenGL / ventana visible
```

El SDK conserva el host de eventos y botones. Se retiró de `host_ui.c` la implementación antigua `n_graficos_circulo`, que había quedado duplicada tras la extracción del módulo FFI.

## 4. Logros funcionales comprobados

### 4.1. Intérprete

- El ejecutable `mictlan` ejecutó `hola_mictlan.lat` desde los directorios de compilación y desde instalaciones aisladas.
- La salida registrada fue: «¡Hola desde Mictlán!», «Bienvenido a Mictlán» y «El resultado es: 42».
- La versión Release compiló con `-O3 -DNDEBUG`. Este dato no demuestra, por sí solo, que sea la mejor combinación de optimizaciones para todos los programas.
- Se aprobaron anteriormente 11 suites de regresión de Core. **No consta una nueva ejecución íntegra de esas suites en el último corte**.

### 4.2. Interfaz gráfica y dibujo

- Raylib/GLFW/OpenGL inicializaron una ventana real en Debian.
- Las acciones de Mictlán Lab «Preparar escena» y «Reiniciar» funcionaron.
- El círculo naranja solicitado mediante `graficos.circulo(680, 360, 45, 230, 110, 60)` fue visible.
- Se separaron el almacenamiento, el renderizador y el puente FFI.
- Las **25 pruebas del SDK pasaron (0 fallos)** tras la refactorización. La última batería completa compartida tardó **1,66 s**; antes de este informe también se validó la FFI de forma individual.
- El lienzo actual mantiene una capacidad fija de 128 círculos, según los informes previos.

### 4.3. Estado real de las pruebas

| Comprobación | Resultado observado | Alcance |
|---|---|---|
| SDK / CTest | 25/25, 0 fallos | Funciones y escenarios automatizados existentes |
| FFI `graficos.circulo()` | `FFI_GRAFICOS_OK` | Casos válidos e inválidos definidos en la prueba |
| Prueba visual | Círculo visible, botones operativos, cierre normal | Una aplicación y el equipo actual |
| Core: suites heredadas | 11 suites aprobadas anteriormente | No repetir como si fueran una prueba actual de Release |
| Distribución portable | Extracción y «resultado 42» | Mismo sistema anfitrión, no otra distribución |

**Deuda de pruebas:** reforzar la prueba FFI para verificar código de salida y estado efectivo, ampliar casos límite; introducir CI; repetir regresiones de Core en Release y Debug; ejecutar pruebas instrumentadas (ASan/UBSan) y comprobar la distribución en sistema limpio.

## 5. Optimización y accesibilidad para hardware modesto

El proyecto persigue dos perfiles: **Core ligero** (consola, sin GPU obligatoria) y **Graphics opcional** (ventanas y renderizado). Esta distinción impide imponer Raylib y sus dependencias a quien solo desea aprender programación básica.

### Mediciones iniciales de memoria del ejemplo mínimo

| Perfil | Ejecución 1 | Ejecución 2 | Ejecución 3 | Pico RSS promedio aproximado |
|---|---:|---:|---:|---:|
| Debug | 2952 KB | 2804 KB | 2880 KB | 2879 KB |
| Release | 2716 KB | 2724 KB | 2844 KB | 2761 KB |

Con esos tres ensayos, Release presentó un promedio aproximadamente **4,1 % menor** de pico de memoria residente. El ejemplo terminó con tiempos reportados como `0.00 s`, insuficientes para comparar velocidad. Son **mediciones exploratorias**, no requisitos mínimos, ni un benchmark significativo de programas grandes.

### Tamaños observados (no comparables entre sí sin contexto)

| Elemento | Tamaño observado | Interpretación |
|---|---:|---|
| Ejecutable `mictlan` Debug | 498K | Solo archivo ejecutable |
| Ejecutable `mictlan` Release | 234K | Solo archivo ejecutable |
| Primera instalación Core completa | 1.5M | Incluye bibliotecas, cabeceras y recursos heredados |
| Portable manual | 252K | Ejecutable y ejemplo |
| Portable CMake mínima | 260K | Ejecutable y ejemplo, con ocupación de directorios |
| Portable documentada | 276K | Ejecutable, ejemplo, README y licencia |
| Paquete TAR automatizado | 96K | Archivo comprimido de la última ejecución |

Los tamaños vienen de `ls -lh` o `du -sh`, por lo que son aproximados y con redondeos. La reducción del ejecutable Release frente a Debug ronda el 53 %, **sin implicar una reducción equivalente del uso de RAM o del tiempo de ejecución**.

## 6. Evolución de la distribución y su automatización

| Paso | Estado | Evidencia |
|---|---|---|
| Instalación completa aislada | Verificada | `cmake --install` instaló `mictlan` y recursos heredados; ejemplo correcto |
| Copia portable mínima | Verificada | Dos archivos; ejemplo correcto fuera del repositorio |
| Componente `MictlanPortable` | Verificado | `cmake --install --component MictlanPortable` |
| Manual y licencia incorporados | Verificado | Cuatro archivos en instalación documentada |
| Primer TAR manual | Verificado | Archivo de 95K, listado, extraído, ejecutado, SHA-256 calculado |
| Script `empaquetar_portable.sh` | Verificado | Compila, instala, empaqueta, comprueba hash, extrae y ejecuta |
| Último TAR automático | Verificado localmente | Archivo de 96K, SHA-256 coincide, resultado 42 |
| `.deb` de Mictlán | **No creado todavía** | Herramientas presentes; metadatos por adaptar |
| Instalador gráfico o Windows/macOS | **No creado todavía** | Objetivo posterior |

**Último artefacto conocido:** `~/Proyectos/Mictlan/artefactos/lote-FCZa2C/mictlan-0.1.0-alpha-linux-x86_64.tar.gz` (96K, nombre y lote según salida de la terminal). Este nombre provisional **no debe tratarse aún como publicación oficial**.

**Atención a las dependencias:** el ejecutable de consola usa bibliotecas del sistema, entre ellas `libc`, `libm`, `libreadline` y `libtinfo`; el host gráfico usa además `liblatino.so` desde la compilación de Core y `libraylib.so.620` ubicada en `/usr/local/lib` del equipo probado. Por ello, copiar `host_ui` aislado **no basta para distribuir Graphics**.

### Limitaciones de automatización detectadas

- El script emplea directorios `mktemp` y deja datos temporales después de finalizar: crear una política de limpieza segura.
- El `.tar.gz` todavía no es necesariamente reproducible byte a byte; normalizar orden, marcas de tiempo, propietario y compresión antes de publicar.
- El script verifica el ejemplo y la coincidencia de SHA-256, pero falta una prueba más exigente de funciones habituales y errores controlados.
- El empaquetado está separado del registro Git; asociar futuras versiones a un commit y una etiqueta verificables.
- La distribución sigue dependiendo de bibliotecas compatibles presentes en el sistema destino; hay que probarla en una instalación limpia.

## 7. Licencias, atribuciones y procedencia

**Licencias raíz observadas:** `mictlan-core/LICENSE` contiene MIT con copyright de **lenguaje latino (2021)**; `mictlan-sdk/LICENSE` contiene MIT con copyright de **Tuxmatic (2026)**. Las condiciones esenciales MIT permiten modificación y redistribución conservando los avisos aplicables. La titularidad sobre las aportaciones originales no elimina los derechos de autores de código heredado.

**Avisos adicionales identificados:** `latparse.c` y `latparse.h` contienen copyright de la Free Software Foundation y la excepción especial del esqueleto de GNU Bison; `latcurseslib.c` contiene un aviso de Lenguaje-Latino (2019) y cláusula referente al uso de nombres para promoción. La excepción Bison evita inferir automáticamente que todo Mictlán deba cambiar a GPL por contener el analizador generado; aun así hay que conservar y revisar los avisos adecuados.

**Auditoría pendiente antes de la distribución pública:** enumerar código de terceros compilado, verificar las condiciones y el texto completo de las licencias aplicables, preparar un `copyright` completo para distribución, y diferenciar atribuciones de Latino y de Tuxmatic. No basta con localizar archivos llamados `LICENSE`.

## 8. Historial Git y puntos de recuperación

| Repositorio | Rama local | Último commit confirmado | Estado conocido |
|---|---|---|---|
| `mictlan-core` | `desarrollo/mictlan-alpha` | `e9c7894` — `build(mictlan): automatizar empaquetado portable` | Limpio tras el commit |
| `mictlan-sdk` | `desarrollo/mictlan-alpha` | `ea375e3` — `refactor(graphics): separar FFI del host grafico` | Limpio en su última inspección |
| `mictlan-lab` | `main` | `d5f22b8` — `feat(lab): validar primer circulo desde Mictlan` | Limpio en su última inspección |

**Commits recientes de Core:** `5f02d81` (componente de instalación portable), `8e80c0a` (manual y licencia), `e9c7894` (script). **Commits destacados del SDK:** `385c720` (biblioteca 2D), `41ed91f` (renderizador), `9e63c72` (FFI inicial), `1bdf18f` (prueba FFI), `ea375e3` (extracción FFI).

Los commits citados son **locales** según la evidencia; no consta confirmación de `git push` ni un lanzamiento en GitHub. Anteriormente se crearon bundles Git y copias de archivos históricos, pero conviene actualizar los respaldos antes de la publicación.

## 9. Diagnóstico del empaquetado Debian: riesgo inmediato

Las herramientas están presentes: **CMake/CPack 3.31.6**, `/usr/bin/dpkg-deb`, `/usr/bin/dpkg-shlibdeps`; `dpkg --print-architecture` devolvió **amd64**.

No obstante, `mictlan-core/src/CMakeLists.txt` aún utiliza variables heredadas: nombre de paquete `Latino`, versión `LATINO_VERSION` (mostrada como 1.5.0.0), proveedor Lenguaje-Latino, descripción, web y responsable antiguos, generadores `DEB;RPM;TGZ`, y `CPACK_DEBIAN_PACKAGE_NAME` establecido en `latino`. Además, las reglas completas instalan recursos y archivos de desarrollo heredados.

**Riesgo:** ejecutar inmediatamente `cpack -G DEB` con esa configuración podría generar un paquete mal identificado o con un conjunto de archivos no deseado. **No está demostrado que ese comando genere ya un `.deb` correcto de Mictlán.**

**Precaución de orden:** `include(CPack)` se encuentra antes de una asignación de `CPACK_INSTALL_CMAKE_PROJECTS` que aparece al final del mismo archivo. Como `include(CPack)` genera `CPackConfig.cmake` durante la configuración, es necesario revisar qué variables efectivamente quedaron registradas antes de confiar en el resultado.

**Diseño preferido:** aislar el paquete de consola `mictlan` de los archivos de desarrollo y de los recursos heredados, definir identidad y versión propias, declarar dependencias automáticas mediante `dpkg-shlibdeps`, e inspeccionar el contenido y el control del `.deb` antes de instalarlo. Un `.deb` debe utilizar la arquitectura Debian **amd64** (que corresponde a x86_64), aunque el artefacto TAR conserve el nombre `linux-x86_64`.

## 10. Estimación orientativa de avance

El informe 01 estimó **53 %** de preparación para una alfa Debian con ejecución de consola y UI sencilla. Para comparabilidad se mantiene la misma ponderación, pero **todas las cifras siguientes son juicios de planificación**, no mediciones de código completado.

| Área | Peso original | Informe 01 | Preparación actual estimada | Aporte actual |
|---|---:|---:|---:|---:|
| Intérprete y compatibilidad básica | 20 % | 90 % | 90 % | 18,0 |
| UI y host gráfico existentes | 20 % | 85 % | 90 % | 18,0 |
| Dibujo 2D mínimo para Lab | 10 % | 25 % | 90 % | 9,0 |
| Experiencia de uso y comandos públicos | 10 % | 40 % | 60 % | 6,0 |
| Instalación y distribución | 20 % | 0 % | 45 % | 9,0 |
| Documentación de usuario | 10 % | 45 % | 65 % | 6,5 |
| Pruebas e integración | 10 % | 70 % | 80 % | 8,0 |
| **Total orientativo** | **100 %** | **53 %** | | **74,5 % (~75 %)** |

La estimación muestra avance desde el informe 01, pero **no equivale a completar el 75 % de un lenguaje de propósito general comparable en ecosistema con Python, Java o C++**. Sin requisitos cerrados para redes, paquetes, web, GUI avanzada, GPU, 3D, depurador y múltiples sistemas operativos, ese porcentaje total no puede calcularse honestamente.

**Dos metas separadas:** (a) alfa de consola para Debian, cercana a una entrega experimental por disponer de un TAR verificable; (b) alfa integral con distribución de GUI, más trabajo pendiente. No debemos anunciar la segunda como completada por tener lista la primera.

## 11. Pendientes priorizados y criterios de aceptación

### P0. Imprescindibles para una alfa pública de consola

1. **Identidad y versionado:** declarar Mictlán `0.1.0-alpha` de forma consistente en README, programa, instalador y nombre de paquete, preservando referencia a Latino como base. Comprobar la salida real de la versión.
2. **Auditoría de licencias:** consolidar titulares, avisos de Bison y terceros, y archivo `copyright` de la distribución. No alterar ni eliminar atribuciones originales.
3. **Empaquetado Debian aislado:** preparar configuración CPack específica para Mictlán, con solo Runtime, sin incluir SDK por accidente; generar `.deb` en un directorio de trabajo temporal.
4. **Inspección sin instalación:** verificar metadatos y lista de archivos del `.deb` mediante `dpkg-deb --info` y `dpkg-deb --contents`; comprobar dependencias detectadas.
5. **Prueba de instalación limpia:** en VM/contenedor o equipo de prueba Debian compatible, instalar, ejecutar varios `.lat`, desinstalar y comprobar que los proyectos del usuario permanecen intactos.
6. **Calidad mínima:** repetir suites de Core y SDK, probar errores de archivos e instrucciones, memoria en Release, y publicar limitaciones conocidas.
7. **Publicación:** etiqueta Git, README claro, requisitos, aviso experimental, archivos y SHA-256; verificar que los tres repositorios estén respaldados y que el artefacto publicado corresponda a la revisión documentada.

### P1. Distribución gráfica opcional

8. Compilar Graphics para distribución y empaquetar o declarar Raylib/GLFW/OpenGL y `liblatino.so`, sin depender de rutas personales ni de `/usr/local/lib` del desarrollador.
9. Probar apertura, eventos, dibujo, cierre y fallos de GPU; ofrecer una alternativa no gráfica en equipos incompatibles.
10. Publicar `mictlan-ui` y sus ejemplos como componente separado cuando sus dependencias estén resueltas.

### P2. Evolución del lenguaje de propósito general

11. Más primitivas 2D, actualización temporal, entrada, recursos, colisiones y sonido.
12. Biblioteca estándar para red, procesos, archivos, serialización y paquetes, con pruebas por módulo.
13. Herramientas de depuración, editor/IDE opcional, documentación de APIs y plataforma de extensiones.
14. Evaluación de Windows, macOS, ARM y compatibilidad gráfica en equipos antiguos después de validar las compilaciones propias.

## 12. Ruta de trabajo propuesta hasta la alfa

| Fase | Entregable verificable | Criterio de salida |
|---|---|---|
| 1. Congelar y auditar | Inventario de repositorios, licencias y metadatos | Sin cambios no guardados; atribuciones registradas |
| 2. Preparar Debian | `.deb` de consola correctamente identificado | Contenido, dependencias y versión inspeccionados |
| 3. Validar instalación | Registro de prueba limpia, instalación y retiro | Ejecuta programas sin rutas del desarrollador |
| 4. Documentar y publicar | Release experimental con SHA-256 y notas | Descarga, extracción o instalación reproducible para el usuario |
| 5. Continuar Graphics | Paquete gráfico opcional | Funciona fuera del entorno de desarrollo |

**Horizonte:** la fecha del 2 de diciembre de 2026 es una meta tentativa, no una garantía. Priorizar primero una alfa de **consola** evita retrasarla por características gráficas avanzadas o compatibilidad multiplataforma todavía no probada.

## 13. Comprobaciones recomendadas antes del siguiente cambio

Estos comandos son de solo lectura, con excepción de las compilaciones/pruebas cuando se ejecuten por separado. Deben usarse en la terminal integrada de VS Code:

```bash
cd ~/Proyectos/Mictlan

# Estado de los tres repositorios.
for repositorio in mictlan-core mictlan-sdk mictlan-lab; do
    echo "===== $repositorio ====="
    git -C "$repositorio" status --short --branch
    git -C "$repositorio" --no-pager log -1 --oneline
done

# Archivo de configuración generado realmente por CPack.
find build-core-release -name CPackConfig.cmake -print

# Variables heredadas que CPack incorporó al configurarse.
grep -E 'CPACK_(PACKAGE_NAME|PACKAGE_VERSION|DEBIAN_PACKAGE_NAME|GENERATOR|INSTALL_CMAKE_PROJECTS)' \
    build-core-release/CPackConfig.cmake || true
```

Si `CPackConfig.cmake` no se encuentra en la raíz, utilizar la ruta que muestre `find`; no suponer que las variables fuera de ese archivo ya forman parte del paquete. **Todavía no ejecutar `cpack -G DEB` ni instalar con `sudo` hasta aislar y revisar la configuración.**

## 14. Conclusión del hito

Mictlán ya no es únicamente un intérprete local: dispone de **una ruta repetible para producir una distribución pequeña y verificable**, mientras que su SDK ofrece ventanas interactivas y una función gráfica propia probada. La separación Core / SDK / Lab y los commits frecuentes permiten progresar sin mezclar responsabilidades.

El cuello de botella para la alfa dejó de ser dibujar el primer círculo o ejecutar el primer programa. Ahora es **conseguir un paquete identificado, legalmente documentado, con dependencias correctas y probado fuera de la computadora de desarrollo**. Ese será el siguiente hito técnico.

**Título previsto para el informe 04:** «Mictlán encuentra su destino: instalación Debian y primera alfa reproducible»; solo se emitirá cuando exista un `.deb` inspeccionado y probado.

---

## Referencias y fuentes

**Evidencia primaria del proyecto:**

- `Mictlan_Informe_01_El_lienzo_toma_forma_2026-11-06.md` (aportado por el usuario).
- `2026-11-06_02_del_lenguaje_al_pixel.md` (aportado por el usuario).
- Salidas de terminal compartidas hasta el 6 de noviembre de 2026: Git, CMake, CTest, GNU Time, instalaciones aisladas, `tar` y SHA-256.

**Documentación técnica consultada (fuentes oficiales):**

- CMake `install()`, componentes y `EXCLUDE_FROM_ALL`: https://cmake.org/cmake/help/latest/command/install.html
- Módulo CPack y generación de `CPackConfig.cmake`: https://cmake.org/cmake/help/latest/module/CPack.html
- Generador CPack DEB: https://cmake.org/cmake/help/latest/cpack_gen/deb.html
- Política Debian sobre dependencias binarias: https://www.debian.org/doc/debian-policy/ch-binary.html
- Política Debian sobre bibliotecas compartidas: https://www.debian.org/doc/debian-policy/ch-sharedlibs.html
- GNU Tar, archivos reproducibles: https://www.gnu.org/software/tar/manual/html_node/Reproducibility.html

**Carácter del documento:** informe de avance técnico; no certificación de seguridad, auditoría legal completa ni garantía de compatibilidad con otros sistemas operativos.

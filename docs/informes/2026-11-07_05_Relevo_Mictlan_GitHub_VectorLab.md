# MICTLÁN | ACTA DE RELEVO 05
## Continuidad del proyecto en una conversación nueva

**Fecha de referencia:** 7 de noviembre de 2026 (zona horaria de Ciudad de México)  
**Estado:** primera publicación de Core, SDK y Lab en GitHub completada; VectorLab 0.3 en desarrollo local.  
**Propósito de este documento:** transmitir el estado del proyecto, lo demostrado, lo pendiente y la forma segura de continuar. **Este documento no sustituye la revisión del código más reciente ni de los cambios sin commit en el equipo local.**

> **Distinción esencial:** abrir una nueva conversación de ChatGPT **no crea una rama de Git**. Los tres repositorios ya tienen sus propias ramas. El objetivo aquí es continuar el trabajo en un chat nuevo con contexto suficiente.

---

## 1. Propósito y criterios de diseño

**Mictlán** es un proyecto para desarrollar un lenguaje de programación de **propósito general**, basado inicialmente en Latino, pero con identidad, herramientas y capacidades progresivamente propias. El lenguaje debe ser comprensible en español, accesible a principiantes y práctico en equipos modestos, sin renunciar a robustez, extensibilidad y calidad técnica.

**Objetivos a largo plazo:** programación general (aplicaciones y scripts), interfaces de usuario, gráficos y aplicaciones interactivas; computación científica, simulaciones, análisis de datos y métodos numéricos; desarrollo y aplicación de inteligencia artificial; facilidad de instalación, actualización y desinstalación en Linux, Windows y macOS y, eventualmente, otras arquitecturas; optimización de consumo de memoria y tiempo de ejecución; buenas herramientas de desarrollo y documentación. Ninguna de estas metas futuras debe confundirse con características ya terminadas.

**Identidad:** extensión principal `.mict`; se admite `.lat` por compatibilidad. Se desarrolló iconografía cultural inspirada en el símbolo *Miquiztli* y soporte local en VS Code y el gestor de archivos de Debian. El futuro reconocimiento «Mictlán» en la barra **Languages** de GitHub dependerá de GitHub Linguist y no está conseguido por el simple hecho de registrar `.mict` en VS Code.

**Forma de enseñar y trabajar:** la persona responsable del proyecto está aprendiendo programación, Git, CMake y VS Code. Dar instrucciones comprensibles, explicar cada paso en lenguaje sencillo, indicar en cuál carpeta y ventana se ejecuta, mostrar qué resultado debe aparecer, comprobar antes de cambiar de etapa y evitar introducir modificaciones simultáneas en varias áreas. No asumir que domina comandos ni conceptos.

---

## 2. Arquitectura, carpetas y repositorios

Directorio raíz **del equipo local**: `/home/tuxmatic/Proyectos/Mictlan` (`~/Proyectos/Mictlan`).

| Componente local | Repositorio remoto privado | Responsabilidad |
|---|---|---|
| `mictlan-core` | https://github.com/TuxMatic99/Mictlan-Core | Intérprete y máquina virtual derivados de Latino, extensión `.mict`, compilación del núcleo y empaquetado |
| `mictlan-sdk` | https://github.com/TuxMatic99/Mictlan-SDK | Bibliotecas de interfaces, gráficos 2D y ciencia; enlaces FFI; pruebas; complemento VS Code; informes |
| `mictlan-lab` | https://github.com/TuxMatic99/Mictlan-Lab | Programas `.mict`, experimentos visuales/científicos y tareas de VS Code |

Carpetas generadas del directorio raíz: `build-core-debug`, `build-core-release`, `build-sdk-debug`, `build-deb-local`, `artefactos`. No confundirlas con los repositorios de código fuente ni editar directamente sus archivos generados para hacer cambios permanentes.

**Remotos de Git locales:** `github` apunta al repositorio GitHub correspondiente. En Core, `origin` sigue apuntando a `/home/tuxmatic/Respaldos-Mictlan/latino-core.bundle`; en SDK, `origin` apunta a `/home/tuxmatic/Respaldos-Mictlan/LatinoVox.bundle`. Estos respaldos `.bundle` deben conservarse. Lab tiene `github` y no tenía `origin` en la última comprobación. No sustituir `origin` sin motivo.

**Historial de procedencia:** Core conserva la historia de Latino; SDK conserva la de LatinoVox; Lab tiene historia propia. No fusionar historiales ni sustituir repositorios por el antiguo `https://github.com/TuxMatic99/LatinoVox.git` o por `latino-Core`.

---

## 3. Estado remoto VERIFICADO en GitHub

Estos datos se consultaron directamente a través de la conexión autorizada con GitHub, después de los primeros `git push`. Los tres repositorios están **privados**, con rama remota principal `main`.

| Repositorio | Último commit de `main` verificado | Descripción |
|---|---|---|
| **Core** | `b3be302bbfdc0dfc371b6871dd203f7ff9ce3a0b` | `test(core): proteger extensiones mict y lat` |
| **SDK** | `4648f8d92d10b584ac52daacf879a249a28caddd` | `docs(progress): registrar informe 04 de Mictlan` |
| **Lab** | `8a5233b4417fc6971a3ddd51b552d6e948fce50d` | `feat(lab): validar producto punto desde Mictlan` |

Los últimos recuentos locales eran **71 commits Core + 46 SDK + 6 Lab = 123 commits** (historiales de repositorios distintos). El usuario comprobó mediante `git ls-remote` y `git rev-parse HEAD` que las tres ramas remotas `main` coincidían con sus commits locales después de la publicación.

**Limitación:** los archivos editados o creados localmente sin commit **no** forman parte de estos estados remotos. ChatGPT puede consultar el código publicado en GitHub mientras la conexión autorizada esté disponible, pero no ve automáticamente modificaciones locales ni recibe actualizaciones en tiempo real. En una conversación nueva, **volver a consultar los repositorios**, sin asumir que el estado sigue siendo el mismo.

### Archivos remotos revisados

- Core `src/latast.c`: extensión `.mict` y compatibilidad `.lat`; `src/latino.c`: ejecución y códigos de salida.
- SDK `src/ciencia/mictlan_ciencia_ffi.c`: funciones expuestas `ciencia.longitud2()` y `ciencia.producto_punto2()`; `include/mictlan_vectores2d.h`: operaciones vectoriales en C; `CMakeLists.txt`: ejecutor y pruebas científicas.
- SDK `herramientas/vscode-mictlan/package.json`: complemento experimental del lenguaje para VS Code, versión `0.1.0`.
- SDK `docs/informes/2026-11-07_04_Informe_de_progreso_Mictlan.md`: informe de progreso oficial ya publicado.
- Lab `.vscode/tasks.json`: tarea predeterminada «Mictlán: ejecutar programa científico» usando `${workspaceFolder}/../build-sdk-debug/mictlan_ciencia_consola` y `${file}`.
- Lab `aplicacion/vectorlab.mict`: experimento original de longitud vectorial; `pruebas/producto_punto.mict`: producto punto 63 y 0.

---

## 4. Capacidades demostradas y límites

### Núcleo y extensión

- Se ha compilado y ejecutado `build-core-debug/mictlan` en Debian.
- Se verificaron programas `.mict` y `.lat` válidos con código de salida `0`.
- Se verificaron extensiones no admitidas, nombres sin extensión y archivos inexistentes con código de error `1`. Se guardó una prueba de regresión en `mictlan-core/tests/run_extension_regression.sh`.
- Se compiló `liblatino.so`, biblioteca compartida utilizada por el SDK.
- **Pendiente:** limpiar referencias de marca heredadas, evolucionar especificación y herramientas propias, reforzar robustez del lector y memoria, ampliar pruebas.

### Gráficos y UI

- SDK posee infraestructura de diseño, árbol, eventos, callbacks, catálogo, pruebas y una biblioteca de dibujo 2D.
- Un programa pudo registrar un círculo a través de la FFI gráfica y visualizarse en el host Raylib. Se separó la FFI gráfica de `host_ui.c`.
- **Pendiente:** integración coherente de funciones científicas y gráficas en una experiencia general; pruebas adicionales de plataformas.

### Ciencia (VectorLab)

Biblioteca C `mictlan-sdk/src/ciencia/vectores2d.c` con interfaz `include/mictlan_vectores2d.h`:

| Operación | Existe en C | Expuesta en `.mict` al último commit publicado |
|---|---|---|
| Longitud vectorial | Sí | **Sí**, `ciencia.longitud2(x, y)` |
| Producto punto | Sí | **Sí**, `ciencia.producto_punto2(ax, ay, bx, by)` |
| Suma vectorial | Sí | **No** en el último commit publicado; trabajo experimental local |
| Multiplicación escalar | Sí | No |
| Normalización | Sí | No |

El programa `mictlan_ciencia_consola` registra el módulo científico, enlaza con `liblatino.so` y permite ejecutar ejemplos `.mict`. **No equivale a que el intérprete ligero genérico del Core incluya automáticamente ese módulo.**

Resultados comprobados: `longitud2(3,4)=5`, `longitud2(5,12)=13`, `producto_punto2(3,4,5,12)=63`, producto punto de vectores perpendiculares `0`.

**Pruebas automáticas:** último ciclo completo confirmado del SDK: **28/28 pruebas aprobadas, 0 fallos, tiempo de pruebas 1,80 s**. Estos números son anteriores a la integración experimental de `ciencia.sumar2()` y no certifican esa nueva función.

**Experimento VectorLab 0.3 de aritmética dentro de `.mict`:** comprobó `(3,4)+(5,12)=(8,16)` y `2·(3,4)=(6,8)`. Esa ejecución utiliza operadores aritméticos directamente en `.mict`, **no prueba todavía el nuevo retorno de listas de la FFI en C**.

### Herramientas

- Complemento experimental VS Code `tuxmatic.mictlan-language@0.1.0`: lenguaje `.mict`, gramática inicial, archivos con íconos.
- En Debian se registró MIME `text/x-mictlan`; el usuario vio íconos en VS Code y gestor de archivos.
- **Problema de entorno ya identificado:** si se presiona `Ctrl + Shift + B` desde una ventana abierta con `mictlan-sdk`, puede lanzarse una tarea antigua `cmake --build build --parallel && ./build/motor` que falla porque `mictlan-sdk/build` no existe. La tarea correcta está en **Lab**, archivo `mictlan-lab/.vscode/tasks.json`, y debe ejecutarse desde un espacio de trabajo Lab con un `.mict` activo. Hubo una propuesta de crear `Mictlan.code-workspace` unificado, pero **no se confirmó que dicho archivo haya sido instalado correctamente en la computadora**.

### Distribución, rendimiento y licencias

- Se probaron paquetes portables Linux x86_64 y un `.deb` AMD64 experimentales, con ejecución del ejemplo y comprobaciones de dependencias; el `.deb` de prueba pasó Lintian estricto. **Los paquetes son anteriores a modificaciones recientes y deben regenerarse y volver a probarse**.
- Una ejecución trivial tuvo consumo máximo observado aproximado de 2,7–3,0 MB de RAM, pero esto **no demuestra** buen rendimiento para programas reales ni compatibilidad universal con máquinas de pocos recursos.
- Core conserva atribución y licencia MIT de Latino; SDK tiene licencia MIT de Tuxmatic; revisar avisos de Bison y componentes heredados antes de una publicación abierta o paquete general.
- Las capacidades de matrices avanzadas, IA, aprendizaje profundo y múltiples sistemas operativos son **objetivos**, no características implementadas y comprobadas.

---

## 5. Cambios locales todavía pendientes: NO CONFUNDIR CON GITHUB

**Última salida de `git status` compartida antes del primer `push`, pendiente de volver a comprobar:**

- `mictlan-core`: limpio, rama `desarrollo/mictlan-alpha`.
- `mictlan-sdk`: rama `desarrollo/mictlan-alpha`; `M src/ciencia/mictlan_ciencia_ffi.c` (trabajo local de `ciencia.sumar2()`); `?? docs/informes/2026-11-06_03_Mictlan_sale_del_laboratorio.md` (informe antiguo sin seguimiento).
- `mictlan-lab`: rama `main`; `?? pruebas/hola_mictlan.mict`, `?? pruebas/suma_vectorial.mict`, `?? pruebas/vectorlab_03.mict`.

**Información adicional:** se compilaron exitosamente `mictlan_ciencia_ffi` y `mictlan_ciencia_consola` después de agregar provisionalmente `ciencia.sumar2()`; sin embargo, el usuario mostró un error de tarea de VS Code antes de confirmar la ejecución del archivo `suma_vectorial.mict`. **No está validada la salida del nuevo retorno de lista ni existe una prueba de integración guardada para esa función.** No afirmar que está terminada.

Antes de operar sobre los archivos locales, pedir o recibir una salida actualizada de `git status` y preferiblemente `git diff -- src/ciencia/mictlan_ciencia_ffi.c`. Nunca reemplazar ciegamente una edición local solo porque GitHub conserva la versión anterior.

---

## 6. Tarea inmediata para la nueva conversación

**Prioridad A: cerrar VectorLab 0.3, evitando dispersarse.**

1. Verificar el estado actual de Core, SDK y Lab, con especial atención a los archivos locales sin commit.
2. Comprobar que el ejecutable científico está compilado y ejecutar el programa `suma_vectorial.mict` **directamente desde la terminal**, sin depender primero de `Ctrl + Shift + B`:

   ```bash
   cd ~/Proyectos/Mictlan
   cmake --build build-sdk-debug --target mictlan_ciencia_consola --parallel 2
   ./build-sdk-debug/mictlan_ciencia_consola mictlan-lab/pruebas/suma_vectorial.mict
   echo "Código de salida: $?"
   ```

   **Salida matemática esperada:** componentes X=`8`, Y=`16` y código de salida `0`. Si falla, inspeccionar exactamente el código local y los diagnósticos, no inventar una corrección.
3. Revisar la representación de vectores como listas (`latL_crear`, `latL_agregar`, `latC_crear_numerico`, `latC_crear_lista`, `latC_apilar`) y su gestión de memoria, con el código Core como fuente de verdad. No asumir que compilar significa ser seguro ante errores.
4. Crear prueba de integración automatizada de suma vectorial que valide componentes, tipos y código de retorno, más casos límite apropiados; pasar toda la batería CTest.
5. Implementar `ciencia.escalar2()` reutilizando la función de retorno de vectores, agregar prueba propia, ejecutar batería de regresión.
6. Cuando todo pase, guardar commits pequeños y explícitos en SDK y Lab y **publicar deliberadamente** en GitHub. No mezclar el informe antiguo pendiente con cambios científicos.
7. Solo entonces crear informe/acta de nuevo hito y continuar con normalización.

**Prioridad B (después, no ahora):** definir especificación/API de `ciencia`, unificar tareas VS Code, documentación de arquitectura, CI con GitHub Actions y mantenimiento de paquetes.

---

## 7. Comandos de consulta seguros

### Estado Git de todos los repositorios (solo lectura)

```bash
cd ~/Proyectos/Mictlan
for repo in mictlan-core mictlan-sdk mictlan-lab; do
    echo "===== $repo ====="
    git -C "$repo" status --short --branch
    git -C "$repo" log -1 --oneline
    git -C "$repo" remote -v
    echo
done
```

### Compilar y probar el SDK completo (solo compila/ejecuta pruebas)

```bash
cd ~/Proyectos/Mictlan
cmake --build build-sdk-debug --parallel 2 && \
ctest --test-dir build-sdk-debug --output-on-failure
```

### Publicar commits *ya verificados* (NO ejecutar automáticamente)

```bash
# Desde ~/Proyectos/Mictlan y solo tras revisar el estado y los commits:
git -C mictlan-core push github desarrollo/mictlan-alpha:main
git -C mictlan-sdk push github desarrollo/mictlan-alpha:main
git -C mictlan-lab push github main:main
```

Esta sintaxis mantiene el nombre de las ramas locales y envía su contenido a `main` remoto. No utilizar `--force`, `reset --hard`, `clean -fd`, ni sobrescribir archivos locales para resolver diferencias sin análisis previo. Conservar la autenticación a través de GitHub CLI; **no** usar contraseña normal de GitHub para Git HTTPS ni compartir tokens.

---

## 8. Método de trabajo que debe respetar ChatGPT

- Responder en español, con tono docente, explicaciones paso a paso y precisión técnica; la persona usuaria todavía aprende C, Git, GitHub y VS Code.
- **Consultar primero la versión actual en GitHub cuando el contenido remoto sea relevante.** Comparar con resultados locales recientes sin asumir que se han publicado.
- Diferenciar claramente: **(a) código publicado y verificado, (b) pruebas locales observadas, (c) propuestas y metas futuras**.
- Mantener una tarea funcional a la vez. No saltar entre API científica, gráficos, distribución, identidad e IA sin cerrar el hito actual.
- Antes de proponer editar un archivo, indicar su ruta exacta, qué bloque cambiar y qué preservar. Antes de un commit, revisar `git status`, `git diff` y `git diff --check`.
- Explicar comandos, salidas esperadas y posibles errores; preferir pruebas no destructivas. No hacer afirmaciones de éxito sin comprobarlas.
- Recomendar que las pruebas automáticas acompañen cada función nueva; distinguir número de pruebas de su calidad/cobertura.
- No inventar acceso a archivos sin publicar, credenciales ni capacidades de supervisión automática de GitHub.
- Mantener reconocimiento a Latino y conservar los historiales originales; comparar con `https://github.com/TuxMatic99/LatinoVox.git` más adelante sin confundirlo con Mictlán.

---

## 9. Contexto técnico y referencias

**Fuentes directas:** los tres repositorios privados de GitHub (requieren autorización) y salidas de terminal compartidas por la persona usuaria, más el informe 04 existente en SDK.

**Documentación oficial consultada:**

- GitHub: Git y el historial de commits: https://docs.github.com/es/get-started/using-git/about-git
- GitHub: publicación de ramas con nombres distintos: https://docs.github.com/en/get-started/using-git/pushing-commits-to-a-remote-repository
- VS Code: tareas en espacios multi-root: https://code.visualstudio.com/docs/editing/workspaces/multi-root-workspaces
- GitHub Linguist, contribuciones y requisitos: https://github.com/github-linguist/linguist/blob/main/CONTRIBUTING.md

---

## 10. Texto breve para iniciar la nueva conversación

> Estoy continuando el desarrollo de **Mictlán**, un lenguaje de programación de propósito general en español, derivado inicialmente de Latino, con SDK y laboratorio. Soy principiante: explícame todo paso a paso sin asumir conocimientos de programación, Git o VS Code. Adjunto el **Acta de relevo 05**; léela antes de proponer cambios. Mis repositorios privados de GitHub son `TuxMatic99/Mictlan-Core`, `TuxMatic99/Mictlan-SDK` y `TuxMatic99/Mictlan-Lab` (rama remota `main`). Consulta los commits actuales mediante la conexión GitHub y distingue el código publicado de los cambios locales sin commit. Nuestro siguiente objetivo es **cerrar VectorLab 0.3**: verificar la FFI experimental `ciencia.sumar2()`, crear su prueba y después implementar `ciencia.escalar2()`. No alteres las ramas ni hagas commits/push sin revisar los estados. Empecemos comprobando el estado Git local y la ejecución directa de `suma_vectorial.mict`.

**Fin del acta de relevo 05.**

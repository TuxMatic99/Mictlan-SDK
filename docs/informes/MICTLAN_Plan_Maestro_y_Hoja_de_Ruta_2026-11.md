# MICTLÁN | PLAN MAESTRO Y HOJA DE RUTA

**Versión de este documento:** 1.0 de planificación, noviembre de 2026  
**Fuentes:** informes de avance 01, 02, 03, 04, acta de relevo 05; comprobación del código publicado en GitHub; registros locales recientes de compilación y pruebas (29/29).  
**Alcance:** documento de referencia para organizar el desarrollo; no constituye una especificación terminada, un lanzamiento ni una promesa de fechas.

## 1. Visión y alcance

Mictlán será un lenguaje de programación de propósito general, accesible en español, de diseño modular, con aspiración a buen rendimiento en hardware modesto, capaz de ejecutar programas de consola y, mediante bibliotecas opcionales, aplicaciones gráficas, cómputo científico y, posteriormente, aplicaciones de inteligencia artificial.

Se desarrolla inicialmente a partir de Latino. Una extensión `.mict`, un nombre nuevo o un módulo FFI no significan todavía que el lenguaje sea independiente de su base. La evolución hacia una identidad técnica propia debe quedar documentada y probada.

**Dos metas distintas**:
- **Alfa 0.1 para Debian x86_64:** prototipo instalable y utilizable con consola, ejemplos, pruebas, atribución y limitaciones explícitas. La interfaz gráfica y la ciencia pueden ser componentes experimentales separados.
- **Versión 1.0:** lenguaje con especificación estable, API y paquetes definidos, instalación y mantenimiento reproducibles, documentación y calidad suficientes para casos de uso reales. Capacidades de IA, web, 3D y múltiples sistemas son extensiones planificadas, no requisitos para la primera alfa.

La fecha del **2 de diciembre de 2026** fue una propuesta tentativa en el informe 01, **no un compromiso**. Revaluar según los criterios de aceptación.

## 2. Arquitectura que no debemos romper

```text
~/Proyectos/Mictlan/
├── Mictlan.code-workspace          VS Code: área de trabajo unificada
├── mictlan-core/                  Núcleo y ejecutable del lenguaje
├── mictlan-sdk/                   Bibliotecas UI, gráficos, ciencia, herramientas
├── mictlan-lab/                   Programas y experimentos .mict
├── build-core-debug/              Salida generada
├── build-core-release/            Salida generada
├── build-sdk-debug/               Salida generada
└── artefactos/                    Paquetes experimentales
```

**Dependencias:** Lab utiliza SDK; SDK utiliza API de Core; Core no debe depender de Lab ni obligar a instalar gráficos. Las herramientas de VS Code facilitan compilar/ejecutar pero no forman parte del lenguaje. Mantener los tres historiales de Git por separado.

**Repositorios privados:**
- https://github.com/TuxMatic99/Mictlan-Core  — último `main` remoto consultado `b3be302`.
- https://github.com/TuxMatic99/Mictlan-SDK  — último `main` remoto consultado `4648f8d`.
- https://github.com/TuxMatic99/Mictlan-Lab  — último `main` remoto consultado `8a5233b`.

**Atención:** estos commits remotos no incluyen los cambios locales sin commit, como `ciencia.sumar2()` y las pruebas nuevas. El último resultado local compartido fue **29/29 CTest aprobadas**, no 28/28. Antes de realizar una operación Git, comprobar estado actual.

## 3. Inventario de logros comprobados

| Área | Logro | Límite conocido |
|---|---|---|
| Core | Compilación Debug/Release, `.mict` + `.lat`, códigos de error y prueba de regresión, `liblatino.so` | Derivado de Latino; identidad, especificación y robustez por completar |
| SDK gráfico | Infraestructura UI/eventos, lienzo de círculos, Raylib, FFI gráfica modularizada y pruebas | Escena 2D básica; no distribución gráfica completa |
| SDK científico | Funciones C: suma, escalar, longitud, producto punto y normalización | FFI `.mict` publicada solo longitud y producto punto; suma probada **localmente** |
| VectorLab | Longitudes 5/13; producto punto 63/0; suma vectorial 8/16, 0/0 y 2/-8 | Falta probar fallos de entrada, desbordamientos y memoria; escalar FFI pendiente |
| Calidad | Última batería SDK **29/29**, cero fallos, 1,86 s | No equivale a ausencia de errores ni a auditoría de seguridad |
| Editor | VS Code: extensión inicial, MIME, iconos, workspace único con tareas | Sin LSP ni depuración avanzada demostrada |
| Distribución | TAR experimental (~96 KiB) y `.deb` AMD64 experimental que pasó Lintian y ejecución aislada | Paquetes anteriores a cambios nuevos; no se ha demostrado instalación/desinstalación real en sistema limpio |
| Git | Tres repositorios privados con ramas `main` y atribuciones preservadas | Trabajo local sin commit ni actualización remota; documentación raíz heredada |

## 4. Hoja de ruta ordenada: de hoy a la primera alfa

### HITO 0 | Conservación y trazabilidad — realizado en lo esencial
- [x] Recuperar repositorios y respaldar historiales.
- [x] Separar Core, SDK y Lab.
- [x] Publicar por primera vez las tres ramas `main` privadas en GitHub.
- [x] Adoptar un workspace unificado y probar su tarea científica.
- [ ] Asegurar que `Mictlan.code-workspace` quede guardado y documentado en una ubicación compartible/reproducible; no darlo por versionado.

**Salida:** historial preservado, rutas y módulos claros y un entorno de trabajo replicable.

### HITO 1 | VectorLab 0.3: operaciones vectoriales — **ACTUAL**
- [x] Suma vectorial C a través de `ciencia.sumar2()`; retorno de lista y tres escenarios normales, nulos y mixtos.
- [x] Prueba CTest de integración `mictlan_ciencia_suma_vectorial_integracion` aprobada; total **29/29**.
- [ ] Probar y documentar entradas de tipo inválido, no finitos y resultados desbordados; distinguir errores recuperables de abortos de VM.
- [ ] Revisar duración y propiedad de memoria de las listas C; ejecutar ASan/UBSan cuando sea apropiado.
- [ ] Implementar `ciencia.escalar2(x,y,factor)` como FFI, devolver dos componentes; incluir pruebas normales, cero, negativos y errores.
- [ ] Ejecutar de nuevo la batería del SDK y pruebas de Core afectadas.
- [ ] Revisar `git diff`, hacer commits selectivos en SDK y Lab, publicar a GitHub y verificar los SHAs. Conservar informe 03 antiguo sin seguimiento hasta revisarlo.
- [ ] Registrar el cierre del hito y su nuevo número de pruebas.

**Salida:** VectorLab 0.3 funcional y documentado en Git, con integración reproducible y riesgos conocidos.

### HITO 2 | Biblioteca científica mínima coherente
- [ ] Integrar normalización, con tratamiento documentado del vector cero.
- [ ] Estabilizar formato de devolución (listas de dos componentes frente a futuro tipo vectorial) y convenciones de errores.
- [ ] Documentar API, ejemplos y pruebas de precisión (valores extremos, tolerancias, NaN/Inf) y memoria.
- [ ] Introducir matrices pequeñas, estadísticas sencillas y lectura/escritura de datos **después** de cerrar el conjunto de vectores.

**Salida:** pequeño paquete `ciencia` usable y comprensible, sin depender de un ejemplo del Lab.

### HITO 3 | Unificación de ejecución y definición del lenguaje
- [ ] Decidir cómo cargar opcionalmente módulos científicos y gráficos desde el ejecutable de usuario, sin obligar al Core a depender de Raylib.
- [ ] Especificar sintaxis, tipos, estructuras de control, funciones, módulos, archivos, errores y compatibilidad `.lat`.
- [ ] Revisar denominaciones/versiones de Mictlán frente a Latino, manteniendo atribución original.
- [ ] Programas de extremo a extremo que unan Core, FFI y SDK; añadir pruebas por funcionamiento y fallos.

**Salida:** la persona usuaria puede ejecutar programas Mictlán y solicitar módulos sin conocer rutas de desarrollador.

### HITO 4 | Calidad, documentación y automatización
- [ ] Pruebas Core y SDK en Debug/Release; regresiones de parser, archivos, VM y módulos.
- [ ] ASan/UBSan y comprobaciones de memoria; análisis estático cuando resulte útil.
- [ ] Configurar CI para compilar y ejecutar tests automáticamente tras cada push/PR, empezando por Debian/Linux.
- [ ] Reescribir README de Core y SDK (actualmente aún titulados «Latino Core» y «LatinoVox 2D»), sin borrar reconocimiento histórico.
- [ ] Revisar workflow legado `.github/workflows/release.yml` en Core: se activa mediante etiquetas `v*` y puede intentar construir instaladores de plataformas no validadas; no crear etiquetas de lanzamiento hasta revisarlo.
- [ ] Guías `Instalar`, `Hola mundo`, `Usar ciencia`, `Problemas frecuentes`, licencias y contribución.

**Salida:** código comprensible, comprobable de manera repetible y automatizable.

### HITO 5 | Distribución reproducible: alfa Debian de consola
- [ ] Nombre, versión y metadatos del ejecutable/paquetes consistentes, sin reemplazar atribuciones heredadas.
- [ ] Rehacer TAR y `.deb` desde un commit identificado y CI verde.
- [ ] Auditoría de licencias y archivos incluidos, Bison, dependencias C/readline y copyright Debian.
- [ ] Inspeccionar `dpkg-deb --info`, `--contents`, dependencias y SHA-256.
- [ ] Instalar, ejecutar `.mict`, manejar errores, desinstalar en VM/contenedor/instalación limpia, sin depender de rutas personales.
- [ ] Publicar **pre-release** `0.1.0-alpha` con tags, paquetes, hashes, notas y limitaciones. Revisar antes el workflow `release.yml` heredado.

**Salida:** primera versión descargable, instalable y comprobada para Debian x86_64. No prometer Windows o macOS sin pruebas propias.

### HITO 6 | Gráficos opcionales e integración demostrable
- [ ] Distribución gráfica separada con dependencias correctas de Raylib/GLFW/OpenGL.
- [ ] Geometría 2D adicional (línea, rectángulo, colores), eventos, temporización y ciclo de vida.
- [ ] Un programa `.mict` que calcule datos (vectores) y los dibuje en una ventana fuera del directorio de desarrollo.
- [ ] Pruebas en hardware modesto y fallos de GPU; ejemplos y documentación.

**Salida:** módulo gráfico opcional con una demostración científica visual replicable.

## 5. Después de la alfa: crecimiento hacia un lenguaje de propósito general

### HITO 7 | Biblioteca estándar y ecosistema
- [ ] APIs sólidas de archivos, entrada/salida, rutas, texto, Unicode, fecha/hora, matemáticas y colecciones.
- [ ] Módulos/paquetes y dependencias, compatibilidad de API, ejemplos, diagnósticos y errores comprensibles.
- [ ] LSP y autocompletado, depurador, documentación navegable y tutoriales para principiantes.
- [ ] Redes y formatos de datos; procesos y concurrencia según pruebas de seguridad y rendimiento.

### HITO 8 | Ciencia y simulaciones de mayor alcance
- [ ] Vectores N-dimensionales, matrices y álgebra lineal, resolución de sistemas, estadística y métodos numéricos.
- [ ] Formatos CSV/JSON y datos, control de precisión, benchmarks y límites de memoria.
- [ ] Gráficas científicas 2D/3D y simulaciones de dominio con funciones claramente documentadas.

### HITO 9 | IA aplicada e interoperabilidad
- [ ] Integración con bibliotecas externas o APIs mediante FFI/bindings antes de intentar construir desde cero un ecosistema completo.
- [ ] Tensores y operaciones vectorizadas solo cuando matrices, memoria y pruebas estén consolidadas.
- [ ] Ejemplos medibles de inferencia y, más adelante, entrenamiento; valorar hardware y límites sin prometer aceleración universal.

### HITO 10 | Portabilidad, rendimiento y versión 1.0
- [ ] Portar y probar realmente en sistemas seleccionados (Windows, macOS, Linux ARM) de uno en uno.
- [ ] Diseñar benchmarks reproducibles con programas reales y perfiles de memoria.
- [ ] Congelar una especificación inicial del lenguaje y políticas de compatibilidad, documentación, API y distribución estable.
- [ ] Realizar pruebas de regresión, instalación y desinstalación desde cero, informes de defectos y criterios de lanzamiento.

**Definición de 1.0:** lenguaje útil y estable dentro de un alcance explícito y probado. No significa poseer todas las bibliotecas de Python ni todas las capacidades imaginables.

## 6. Prioridad inmediata y próximo comando seguro

**No saltar aún al hito 2 o a empaquetar.** Primero completar memoria/errores y `ciencia.escalar2()`, luego integrar pruebas, hacer commits selectivos y sincronizar GitHub. Solo después elegir la siguiente línea de trabajo. El estado del workspace debe mantenerse unificado en VS Code.

Consulta inicial segura:

```bash
cd ~/Proyectos/Mictlan
for repo in mictlan-core mictlan-sdk mictlan-lab; do
  echo "===== $repo ====="
  git -C "$repo" status --short --branch
  git -C "$repo" log -1 --oneline
  echo
done
```

**Convención de trabajo:** una función a la vez → probar manualmente → automatizar casos normales y errores → revisar C/memoria → probar regresiones → documentar → `git add` selectivo → commit → push explícito → verificar remoto → actualizar el acta de progreso.

## 7. Riesgos a no olvidar

- Una batería de pruebas aprobada no demuestra que no existan errores de memoria, bugs ni riesgos de seguridad.
- Los paquetes antiguos y los `README.md` heredados no reflejan necesariamente Mictlán actual.
- El flujo de etiqueta `v*` de Core es legado; revisar antes de publicar releases automáticas.
- GitHub `main` solo contiene commits enviados; jamás presuponer que refleja modificaciones sin guardar de VS Code.
- Mantener licencia MIT y demás avisos aplicables de Latino y colaboradores; realizar auditoría de terceros antes de lanzar.
- Las afirmaciones de rendimiento basadas en el ejemplo trivial y el «75 %» orientativo del informe 03 no son porcentajes ni benchmarks del lenguaje terminado.

## 8. Fuentes técnicas públicas

- VS Code y workspaces: https://code.visualstudio.com/docs/editing/workspaces/workspaces
- CTest: https://cmake.org/cmake/help/latest/manual/ctest.1.html
- GitHub Actions CI: https://docs.github.com/en/actions/get-started/quickstart
- GitHub Releases y tags: https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases

**Nota de actualización:** verificar los commits y el estado local cada vez que se retome el plan. Este archivo no cambia ni publica los repositorios por sí solo.

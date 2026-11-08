# Mictlán | Informe 04 de progreso

**Fecha de corte:** 7 de noviembre de 2026
**Proyecto:** Mictlán, lenguaje y ecosistema de programación
**Etapa:** Alfa 0.1, desarrollo experimental
**Asunto:** Consolidación del lenguaje, identidad visual, distribución Linux y primer módulo científico
**Base del informe:** resultados de terminal, pruebas y registros Git compartidos durante el desarrollo hasta esta fecha. Las referencias externas explican las herramientas, pero no sustituyen pruebas del código en otra computadora.

---

## 1. Resumen ejecutivo

**Mictlán ya es un prototipo ejecutable, pero todavía no es un lenguaje de propósito general terminado ni una distribución multiplataforma.** Parte del intérprete de Latino y se está diferenciando mediante la extensión `.mict`, nuevas bibliotecas, programas experimentales, herramientas de desarrollo e identidad visual propia.

El hito más reciente es **Mictlán Ciencia / VectorLab 0.2**. Se ha conectado desde programas `.mict` una operación de longitud vectorial y otra de producto punto. El programa de prueba calculó correctamente `63` para `(3, 4) · (5, 12)` y `0` para `(3, 4) · (-4, 3)`. La compilación completa del SDK terminó sin errores y **CTest aprobó 28 de 28 pruebas, con cero fallos, en 1,80 segundos**. Esto valida los casos cubiertos por las pruebas; no garantiza ausencia de todos los defectos.

La integración de VS Code ya identifica archivos `.mict`, presenta el ícono propio y permite ejecutar el intérprete científico con `Ctrl + Shift + B`, siempre que **Mictlán Lab sea el espacio de trabajo abierto**. En Debian, el tipo MIME `text/x-mictlan` está registrado y el ícono aparece en el gestor de archivos usado en las comprobaciones.

Se han preparado también una distribución portable de consola para Linux x86_64 y un paquete Debian AMD64 de prueba. Ambos se extrajeron y ejecutaron satisfactoriamente en el equipo utilizado; el `.deb` superó una comprobación estricta de Lintian sin errores ni advertencias. **Esos paquetes se generaron antes de algunos cambios posteriores en Core y SDK**, por lo que habrá que reconstruirlos y volver a probarlos antes de presentarlos como una versión actualizada.

## 2. Objetivo del proyecto

Construir un lenguaje de programación de propósito general, **accesible en español, ligero, eficiente y fácil de aprender**, que pueda crecer hacia aplicaciones de escritorio, gráficos, investigación científica, simulación, análisis de datos e inteligencia artificial. La accesibilidad para personas que utilizan computadoras modestas es un requisito de diseño, no un resultado ya demostrado para todas las máquinas.

El proyecto también busca una experiencia de instalación y desinstalación sencilla en varios sistemas operativos y una identidad cultural propia inspirada en el Mictlán de la tradición mexica. No se pretende que la identidad cultural reemplace el rigor técnico ni atribuir capacidades que aún no están implementadas.

## 3. Organización del proyecto

| Componente | Papel actual | Estado según las comprobaciones |
|---|---|---|
| `mictlan-core` | Intérprete y núcleo, derivado de Latino; ejecutable `mictlan` | Ejecuta programas `.mict` y conserva compatibilidad con `.lat` |
| `mictlan-sdk` | Bibliotecas y herramientas para interfaces, dibujo y ciencia | Compila; 28 pruebas registradas en CTest y aprobadas |
| `mictlan-lab` | Programas de aprendizaje, experimentos y tarea de VS Code | Ejecuta VectorLab y pruebas científicas |
| `mictlan-sdk/herramientas/vscode-mictlan` | Complemento experimental de VS Code, íconos y asociación de archivos | Reconocimiento visual y del lenguaje comprobados localmente |
| `build-core-*` y `build-sdk-debug` | Directorios de compilación | Se generan a partir del código; no son repositorios de fuentes |
| `artefactos/` | Paquetes y comprobaciones de distribución | Contiene paquetes de prueba creados en etapas anteriores |

**Explicación sencilla:** Core es el motor que interpreta el programa; SDK es la caja de herramientas; Lab es el banco de experimentos; VS Code es el editor desde el que escribimos y ejecutamos código.

## 4. Hitos completados y evidencia

### 4.1. Núcleo y archivos propios

- El ejecutable `mictlan` compila y ejecuta programas en el entorno Debian utilizado.
- Se admiten las extensiones **`.mict` (principal)** y **`.lat` (compatibilidad)**.
- Las pruebas de regresión comprobaron que un archivo `.mict` válido y otro `.lat` válido se ejecutan con código `0`, mientras que una extensión `.txt`, un archivo sin extensión y un archivo inexistente se rechazan con código distinto de cero (`1` en las pruebas).
- Se reconstruyó `liblatino.so`; los símbolos de la API usados por el SDK estaban disponibles.
- La salida de configuración del núcleo seguía mostrando referencias y numeración heredadas de Latino. La diferenciación de la marca y metadatos es un trabajo pendiente.

### 4.2. Interfaces y gráficos

- Existe una infraestructura de interfaz de usuario en el SDK: diseño, árbol de componentes, eventos, callbacks, catálogo y pruebas de integración.
- Se implementó un lienzo 2D y un renderizador basado en **raylib**.
- Se visualizó correctamente un círculo solicitado desde un programa de Mictlán mediante un puente FFI; los botones de la aplicación siguieron funcionando.
- La FFI gráfica se separó del archivo del host en un módulo independiente. Las pruebas existentes siguieron funcionando tras el cambio.

**Límite actual:** el entorno gráfico y el ejecutor científico son componentes diferentes; todavía no se ha demostrado una aplicación que integre todas las funciones científicas y gráficas en un único programa `.mict` distribuible.

### 4.3. Ciencia y matemáticas

En C se implementó una biblioteca de vectores bidimensionales con **suma, multiplicación escalar, producto punto, longitud y normalización**. Sus pruebas unitarias incluyen un caso de protección frente al vector cero.

El puente **FFI** (interfaz de funciones externas: conecta el código del lenguaje con funciones escritas en C) expone actualmente, según el último código y resultados compartidos:

| Función desde `.mict` | Estado | Evidencia |
|---|---|---|
| `ciencia.longitud2(x, y)` | Funcional | `ciencia.longitud2(3, 4)` devuelve `5` y tiene prueba de integración |
| `ciencia.producto_punto2(ax, ay, bx, by)` | Funcional | Devuelve `63` y `0` en dos casos, con prueba de integración |
| Suma de vectores | Existe en C, aún no expuesta en `.mict` | Pendiente |
| Multiplicación escalar | Existe en C, aún no expuesta en `.mict` | Pendiente |
| Normalización | Existe en C, aún no expuesta en `.mict` | Pendiente |

VectorLab 0.1 calculó correctamente las longitudes `5` y `13`. VectorLab 0.2 validó el producto punto en un archivo experimental `.mict`. El ejecutor actual es `build-sdk-debug/mictlan_ciencia_consola`; **el intérprete de consola distribuido desde Core no incorpora automáticamente las nuevas funciones científicas**.

### 4.4. Pruebas automáticas

- Última ejecución completa del SDK: **28/28 pruebas aprobadas, 0 fallos, 1,80 segundos**.
- La prueba 27, `mictlan_ciencia_longitud_integracion`, validó la longitud mediante el ejecutor científico.
- La prueba 28, `mictlan_ciencia_producto_punto_integracion`, ejecutó un archivo `.mict` y verificó su salida: `MICTLAN_PRODUCTO_PUNTO_OK`.
- Se probaron separadamente el comportamiento de extensiones y los códigos de salida del intérprete Core.

Este conjunto es una **red de protección frente a regresiones**: ayuda a descubrir si un cambio posterior rompe comportamientos ya comprobados. No equivale a una certificación de seguridad, portabilidad ni exactitud para todos los casos numéricos.

### 4.5. Experiencia de desarrollo e identidad visual

- Existe un complemento experimental **Mictlán Language 0.1.0** para VS Code, instalado de manera local y detectado como `tuxmatic.mictlan-language@0.1.0`.
- Los archivos `.mict` se reconocen como lenguaje Mictlán y tienen un ícono distintivo inspirado en el signo *Miquiztli*, con versiones para temas claros y oscuros.
- Debian identifica dichos archivos como `text/x-mictlan`, con ícono visible en el gestor de archivos probado.
- `mictlan-lab/.vscode/tasks.json` registra una tarea de ejecución del intérprete científico. `Ctrl + Shift + B` funciona **cuando VS Code tiene abierta la carpeta `mictlan-lab` como espacio de trabajo**. Si se abre únicamente un archivo desde otra ventana, la tarea puede no aparecer.

**Límite:** la extensión todavía no ofrece, de forma comprobada, análisis semántico, autocompletado avanzado, depuración paso a paso ni un servidor LSP para otros IDE.

### 4.6. Distribución, licencias y eficiencia

- Se creó y probó un **paquete portable Linux x86_64** con ejecutable de consola, programa de ejemplo, README, licencia y verificación SHA-256.
- Se desarrolló un script de empaquetado portable y se guardó en Git.
- Se generó un paquete **Debian AMD64 experimental** (`mictlan_0.1.0-0~alpha1_amd64.deb`); las pruebas consistieron en extraerlo sin instalarlo en el sistema, ejecutar el ejemplo y analizarlo con Lintian.
- La última comprobación estricta compartida de Lintian finalizó sin errores ni advertencias. Esto **no significa** que se haya demostrado instalación y desinstalación reales en múltiples equipos.
- Las dependencias observadas del ejecutable portable incluyen bibliotecas del sistema, en particular libc y readline. Por ello **portable no significa universalmente autocontenido**.
- El paquete comprimido experimental ocupaba aproximadamente **96 KiB** y la instalación local documentada aproximadamente **276 KiB**; son mediciones de esas compilaciones, no tamaños garantizados para versiones futuras.
- En el programa trivial de bienvenida se midió un uso máximo aproximado de **2,7 a 3,0 MB de RAM** en ejecuciones anteriores. Los tiempos redondeados a `0.00 s` no permiten extraer conclusiones fiables de rendimiento comparativo.
- El núcleo conserva los avisos y licencia MIT de Latino; el SDK contiene licencia MIT de Tuxmatic. También se localizaron avisos de GNU Bison con excepción especial en los analizadores generados y condiciones de atribución en archivos heredados. Antes de una publicación amplia habrá que revisar todos los avisos aplicables y las dependencias de cada paquete.

## 5. Registros Git relevantes

Los registros siguientes fueron comprobados mediante las salidas compartidas; **no son commits de un único repositorio**, sino de repositorios independientes.

| Repositorio | Commit | Significado |
|---|---|---|
| `mictlan-core` | `b3be302` | Pruebas de regresión para `.mict` y `.lat` |
| `mictlan-core` | `571c0a4` | Reconocimiento de `.mict` y corrección de códigos de salida |
| `mictlan-core` | `3e6046b` | Empaquetado Debian alfa validado con Lintian |
| `mictlan-sdk` | `5ad51d3` | Biblioteca de vectores 2D |
| `mictlan-sdk` | `1c6a5e1` | Ejecutor científico y puente FFI |
| `mictlan-sdk` | `68d20f7` | Identidad visual y soporte experimental para VS Code |
| `mictlan-sdk` | **`e0d7176`** | Producto punto y prueba automática de integración |
| `mictlan-lab` | `5400506` | Tarea de ejecución en VS Code |
| `mictlan-lab` | `3e58e1c` | VectorLab inicial |
| `mictlan-lab` | **`8a5233b`** | Experimento del producto punto |

**Últimos estados mostrados:** SDK en la rama `desarrollo/mictlan-alpha`, con el informe `docs/informes/2026-11-06_03_Mictlan_sale_del_laboratorio.md` aún sin seguimiento; Lab en `main`, con `pruebas/hola_mictlan.mict` aún sin seguimiento. Estos archivos no están dañados: simplemente todavía no se incluyeron en un commit. Antes de guardar este informe, conviene revisar si hay otros cambios nuevos.

## 6. Riesgos y pendientes prioritarios

1. **Pruebas numéricas incompletas.** Incorporar casos de entradas no finitas, desbordamiento, magnitudes extremas y tolerancias para resultados de punto flotante; verificar también códigos de error, no solo textos impresos.
2. **Integración científica limitada.** Hoy se utiliza un ejecutor científico separado. Diseñar cómo registrar el módulo `ciencia` en la ejecución general sin forzar a todos los usuarios a instalar componentes pesados.
3. **Cobertura del lenguaje.** La sintaxis y buena parte del núcleo proceden de Latino. Para afirmar autonomía creciente se necesita una especificación propia, documentación actualizada, compatibilidad explícita y pruebas del comportamiento del lenguaje.
4. **Distribución desactualizada respecto de algunos cambios.** Reconstruir el paquete portable y el `.deb` desde el código más reciente, verificar dependencias, licencias, ejecución de `.mict` y pruebas de instalación y desinstalación en entornos aislados.
5. **Portabilidad no demostrada.** Windows, macOS, Linux ARM y equipos antiguos están en la hoja de ruta, pero aún faltan compilaciones y pruebas reales. Las dependencias de libc/readline y raylib requieren atención especial.
6. **Rendimiento por medir.** Diseñar comparaciones reproducibles con cargas representativas de CPU, memoria e inicio, en vez de extrapolar desde un ejemplo mínimo.
7. **Calidad y seguridad del núcleo.** Revisar robustez de lectura de archivos, errores, gestión de memoria y ciclos de vida de las máquinas virtuales antes de ampliar el uso.
8. **IA e investigación avanzada todavía en fase de diseño.** No hay evidencia en las pruebas compartidas de tensores, operaciones matriciales generales, diferenciación automática, entrenamiento de redes neuronales ni integración con bibliotecas de IA. Deben figurar como objetivos, no funciones actuales.

## 7. Hoja de ruta recomendada

### Próximo hito: VectorLab 0.3

Conectar a la FFI científica **suma vectorial** y **multiplicación escalar**, aprovechando las funciones C ya existentes. Mantener interfaces pequeñas y pruebas que validen valores normales, ceros y errores. Registrar nuevas pruebas en CTest y, solo cuando pasen, hacer commits independientes en SDK y Lab.

### Hito posterior: biblioteca científica coherente

Exponer normalización y operaciones vectoriales de forma consistente; escribir una breve referencia de API de Mictlán; examinar si conviene representar vectores mediante tipos propios, listas o estructuras del lenguaje. Añadir matrices, estadística y entrada/salida de datos de manera incremental, cuidando precisión, memoria y rendimiento.

### Hito de integración

Permitir que el intérprete general invoque bibliotecas científicas y, más adelante, que una aplicación visual combine cálculo y dibujo de vectores. El objetivo es **modularidad**: quien use Mictlán para consola no debería pagar el coste de cargar un entorno gráfico innecesariamente.

### Hito de lanzamiento alfa reproducible

Automatizar pruebas, empaquetado, manifiesto de dependencias, verificaciones SHA-256 y validación en una instalación limpia. Probar explícitamente Linux x86_64 y después otras arquitecturas/sistemas. Publicar versiones con límites y requisitos claramente documentados.

## 8. Próxima acción práctica

**Primero archivar este informe en `mictlan-sdk/docs/informes/`**, sin incluir el informe anterior que aún está sin seguimiento. Después desarrollar VectorLab 0.3. Mantener una ventana de VS Code abierta con `mictlan-lab` cuando se utilice `Ctrl + Shift + B`.

Para una persona que está aprendiendo: **Git** es el historial de cambios; un **commit** es una fotografía identificada de los archivos preparados; **CMake** organiza la compilación; **CTest** ejecuta las pruebas; **FFI** enlaza Mictlán con funciones escritas en C; y una **rama** es una línea de desarrollo dentro de un repositorio.

## 9. Fuentes técnicas consultadas

Estas fuentes sustentan el funcionamiento general de las herramientas, mientras que los resultados específicos de Mictlán proceden de los registros de terminal compartidos:

- CMake, `add_test`: https://cmake.org/cmake/help/latest/command/add_test.html
- CMake, generador Debian de CPack: https://cmake.org/cmake/help/latest/cpack_gen/deb.html
- VS Code, tareas y espacios de trabajo: https://code.visualstudio.com/docs/debugtest/tasks
- VS Code, contribuciones de lenguaje e íconos: https://code.visualstudio.com/api/references/contribution-points
- Git, preparación de cambios: https://git-scm.com/docs/git-add
- GNU Bison, condiciones y excepción de analizadores generados: https://www.gnu.org/software/bison/manual/html_node/Conditions.html

---

**Conclusión:** a fecha de corte, Mictlán dispone de un núcleo ejecutable, extensión propia, infraestructura gráfica, prototipos de distribución Linux, integración local con VS Code y dos operaciones científicas accesibles desde archivos `.mict`. El avance está respaldado por 28 pruebas del SDK aprobadas y commits separados por componentes. El siguiente objetivo es ampliar la biblioteca científica con prudencia, sin confundir aspiraciones de propósito general, rendimiento y capacidades de IA con funcionalidades ya demostradas.

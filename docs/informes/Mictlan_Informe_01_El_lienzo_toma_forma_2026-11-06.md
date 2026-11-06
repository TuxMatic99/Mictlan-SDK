# Informe de avance 01 | El lienzo toma forma

**Proyecto:** Mictlán, lenguaje y ecosistema de programación de propósito general  
**Fecha de corte:** 6 de noviembre de 2026  
**Hito actual:** Primera biblioteca de comandos de dibujo 2D, compilada y comprobada  
**Estado del hito:** Prueba unitaria aprobada; renderizado visual todavía pendiente  
**Objetivo de lanzamiento:** Alfa pública para Debian x86_64, con fecha tentativa del 2 de diciembre de 2026

## 1. Resumen ejecutivo

Mictlán ya posee tres proyectos locales independientes: **mictlan-core** (intérprete), **mictlan-sdk** (bibliotecas y host gráfico) y **mictlan-lab** (aplicación de referencia). El intérprete `mictlan` ejecuta programas `.lat`; el SDK abre ventanas reales con Raylib y recibe eventos; Lab usa esas funciones sin modificar el núcleo.

En el hito más reciente se añadió al SDK una biblioteca estática de dibujo 2D (`libmictlan_dibujo2d.a`) que administra una lista de círculos. Compiló correctamente y su prueba individual pasó. Posteriormente se reconstruyó todo el SDK y **CTest reportó 24/24 pruebas aprobadas, sin fallos, en 0,45 s**.

**Límite de la evidencia:** esta biblioteca todavía **no dibuja círculos en pantalla**, no está enlazada al host para renderizarlos y no expone aún una API gráfica general mediante FFI a los scripts `.lat`.

## 2. Logros comprobados

| Área | Evidencia | Estado |
|---|---|---|
| Recuperación | Historial Git de Latino-Core y LatinoVox respaldado con bundles verificados; datos históricos preservados | Realizado |
| Core | Ejecutable `mictlan` compilado; ejecutó `hola_mictlan.lat` con resultado esperado | Verificado localmente |
| Core: regresiones | 11 suites heredadas aprobadas antes de los cambios de nombre público | Verificado en aquella revisión; conviene repetir antes del lanzamiento |
| SDK | Compilación Debug completa con GCC y CMake | Verificado |
| SDK: pruebas previas | 23 pruebas de UI, eventos, formularios, persistencia y host aprobadas | Verificado |
| SDK: ventana real | Raylib y OpenGL inicializados; botones y eventos probados; cierre normal | Verificado |
| Lab | Repositorio propio y panel `inicio.lat` funcional, con botones Preparar escena y Reiniciar | Verificado |
| Módulo 2D | Biblioteca estática `libmictlan_dibujo2d.a` creada | Verificado |
| Módulo 2D: regresiones | Prueba `mictlan_dibujo2d_basico` aprobada; batería total 24/24 | Verificado |
| Renderizado personalizado | No se ha conectado al host ni probado un círculo real en pantalla | Pendiente |

## 3. Archivos y arquitectura del hito actual

El trabajo nuevo reside en **mictlan-sdk**, no en **mictlan-core**:

- `include/mictlan_dibujo2d.h`: contrato público en C de círculos y lienzo.
- `src/graficos/dibujo2d.c`: inicialización de lienzo y registro validado de círculos.
- `tests/test_mictlan_dibujo2d.c`: pruebas de alta, límites, valores inválidos y reinicio.
- `CMakeLists.txt`: biblioteca `mictlan_dibujo2d` y nueva prueba CTest.

La representación actual utiliza un arreglo con capacidad para **128 círculos**. No reserva memoria dinámica para cada círculo, y rechaza cantidades fuera de capacidad, radios no positivos y coordenadas no finitas.

**Regla de arquitectura:** Lab depende de las APIs del SDK; el SDK depende de Core y del backend gráfico. Core no debe depender de Lab ni contener lógica particular de una aplicación.

## 4. Incidente resuelto y aprendizaje

CMake no encontraba `src/graficos/dibujo2d.c`. La inspección con `ls -lb` reveló un archivo distinto llamado `dibujo2d.c `, con un espacio final invisible. Se creó y guardó el archivo con el nombre correcto, se retiró la copia mal nombrada y la nueva compilación terminó satisfactoriamente. El resultado posterior mostró solo `dibujo2d.c` en el directorio.

**Prevención:** revisar nombres exactos de archivo (`ls -lb`), guardar cambios en VS Code antes de compilar, y verificar rutas con `test -f` cuando CMake informe un archivo ausente.

## 5. Estado del control de versiones

Revisiones conocidas al cierre de los hitos anteriores:

| Repositorio | Rama | Último commit confirmado en la conversación |
|---|---|---|
| `mictlan-core` | `desarrollo/mictlan-alpha` | `3713cd2` |
| `mictlan-sdk` | `desarrollo/mictlan-alpha` | `5f4dbf5` |
| `mictlan-lab` | `main` | `a38db9e` |

**Atención:** el módulo de dibujo y la actualización de CMake del SDK **todavía no tienen un commit confirmado**. La batería 24/24 indica que funcionan localmente, no que hayan sido incorporados a Git. Antes de cerrar el hito, ejecutar `git status --short --branch`, revisar los cambios, actualizar documentación y crear un commit selectivo.

## 6. Cuánto hemos progresado

### Métricas verificables

- **11/11 suites de Core** aprobadas en su verificación anterior.
- **24/24 pruebas de SDK** aprobadas en la última ejecución, **0 fallos**, duración **0,45 s**.
- **2 ejemplos de UI propios** probados en pantalla (`mi_primera_ventana.lat` y `inicio.lat`), además del ejemplo heredado del host.
- **1 biblioteca 2D de comandos** compilada con **1 prueba nueva**. Aún no renderiza.
- **3 repositorios locales** con responsabilidades independientes.

### Estimación de preparación para la alfa pública

**Estimación orientativa: aproximadamente 53%**, tomando como referencia una alfa Debian capaz de instalarse, ejecutar scripts de consola y crear interfaces gráficas sencillas. No es una medición automática ni equivale a estar al 53% de un lenguaje de propósito general terminado.

| Dimensión | Peso | Preparación estimada | Contribución |
|---|---:|---:|---:|
| Intérprete y compatibilidad básica | 20% | 90% | 18,0 puntos |
| UI y host gráfico existentes | 20% | 85% | 17,0 puntos |
| Dibujo 2D mínimo para Lab | 10% | 25% | 2,5 puntos |
| Experiencia de uso y comandos públicos | 10% | 40% | 4,0 puntos |
| Instalación y distribución | 20% | 0% | 0 puntos |
| Documentación de usuario | 10% | 45% | 4,5 puntos |
| Pruebas e integración | 10% | 70% | 7,0 puntos |
| **Total orientativo** | **100%** | | **53,0 puntos** |

Estas ponderaciones son una **herramienta de planificación**, no métricas objetivas de calidad. El producto completo (web, escritorio, juegos avanzados, IDE, redes y 3D) carece todavía de un alcance cerrado que permita calcular honestamente un porcentaje de finalización al 100%.

## 7. Trabajo pendiente y prioridades

### P0: siguiente hito técnico

1. Registrar en Git el módulo 2D y este informe, sin incluir archivos accidentales.
2. Añadir un renderizador del SDK que lea los círculos del lienzo y llame a Raylib **dentro** del ciclo `BeginDrawing`/`EndDrawing`.
3. Conectar el lienzo al host sin alterar la arquitectura del intérprete.
4. Crear un registro FFI mínimo y validado para solicitar círculos desde código `.lat`.
5. Dibujar el primer círculo desde **mictlan-lab**, comprobarlo visualmente y añadir pruebas de regresión.

### P0: requisitos para distribuir la alfa

6. Proporcionar comandos utilizables desde rutas arbitrarias (`mictlan` y futuro `mictlan-ui`).
7. Resolver rutas de carga y empaquetado de `liblatino.so`, Raylib y demás dependencias.
8. Documentar instalación, primer programa, APIs efectivamente disponibles, licencias y limitaciones.
9. Repetir suites relevantes, verificar compilación limpia y pruebas instrumentadas; automatizar verificaciones en CI.
10. Publicar artefactos verificables para Debian x86_64 y un mecanismo para recibir incidencias.

### P1: después del primer círculo

- Rectángulos, líneas, colores y límites del lienzo.
- Actualización temporal y movimiento sin depender de la velocidad del renderizado.
- Selección y arrastre con ratón, transformaciones y colisiones básicas.
- Guardado/carga de escenas con manejo robusto de errores.

### P2: posteriores a la alfa

- Texturas, sonido, cámaras 3D, shaders personalizados, multihilo y plataformas adicionales.
- Servidor HTTP, paquetes y bibliotecas generales como futuros casos de prueba del propósito general.
- IDE o diseñador visual más completo.

## 8. Próxima condición de éxito

**Hito siguiente sugerido: «Del dato al píxel: primer círculo renderizado desde Mictlán».** Se considerará terminado solo cuando:

- un script `.lat` solicite crear un círculo;
- el SDK valide, almacene y renderice la orden con Raylib;
- la ventana muestre la figura y cierre sin errores observados;
- no fallen las pruebas existentes y se añadan las pertinentes;
- el cambio esté documentado y confirmado en Git.

## 9. Reproducción del resultado del informe

Desde `~/Proyectos/Mictlan`, en la terminal integrada de VS Code:

```bash
cmake --build build-sdk-debug --parallel 2
ctest --test-dir build-sdk-debug --output-on-failure
git -C mictlan-sdk status --short --branch
```

Esperado en la revisión probada: **24/24 pruebas aprobadas**. Este resultado no sustituye las comprobaciones instrumentadas ni una instalación limpia.

## 10. Referencias técnicas

- CMake, bibliotecas estáticas: https://cmake.org/cmake/help/latest/command/add_library.html
- CTest, ejecución y reporte de fallos: https://cmake.org/cmake/help/latest/manual/ctest.1.html
- Git, identificación de cambios pendientes: https://git-scm.com/docs/git-status

---

**Convención de informes futuros:** un número correlativo y un subtítulo nuevo que describa el hito alcanzado. Por ejemplo, «Informe de avance 02 | Del dato al píxel» o «Informe de avance 03 | La primera escena interactiva». No reutilizar el mismo título para hitos diferentes; sí conservar el mismo esquema de evidencias, riesgos y próximos pasos.

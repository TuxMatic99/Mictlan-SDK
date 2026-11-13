# Hoja de ruta de Mictlán

**13 de noviembre de 2026.** Documento rector para priorizar el trabajo. Los cambios pasan por pruebas comparativas y revisión independiente. Las fechas tentativas de informes anteriores eran estimaciones de planificación.

## Decisiones confirmadas

Mictlán deriva de Latino con licencia MIT y comenzó en español. Core, SDK y Lab mantienen historiales separados. El ejecutor base puede compilarse sin Raylib. El SDK incorpora ciencia, UI y gráficos mediante registros FFI. La extensión principal es `.mict` y `.lat` conserva compatibilidad comprobada con programas originales. El nombre de la biblioteca histórica es `liblatino.so`. La API experimental de P0.2-G usa raíces explícitas y queda optativa. El SDK registra pruebas de errores, memoria, ABI y carga científica en CI.

El plan maestro de noviembre documenta los hitos de VectorLab, la primera ventana, la extensión del editor y los paquetes previos. En la revisión actual los repositorios son públicos. Los resultados antiguos de 24/24 y 29/29 corresponden a etapas anteriores del SDK. [Plan maestro histórico](../informes/MICTLAN_Plan_Maestro_y_Hoja_de_Ruta_2026-11.md) · [Informe de progreso](../informes/2026-11-07_04_Informe_de_progreso_Mictlan.md).

## Prioridades y dependencias

| Nivel | Trabajo propuesto | Depende de |
| --- | --- | --- |
| P0 · Alpha | Identidad y versión del producto, corpus Latino, recuperación de VM, política ABI, matriz estricta, instalación Debian y documentación inicial. Revisar límites de cadenas internadas, recompilación y fallos de reserva. | Revisiones experimentales exactas, aceptación del ZIP, revisión independiente de memoria y compatibilidad. |
| P1 · Lenguaje y herramientas | Especificar coerciones, alcance, errores y módulos. Estabilizar la API de GUI, eventos y ventanas. Completar ciencia vectorial y después matrices y estadística. Mejorar resaltado y diagnóstico del editor. | Alpha reproducible, contratos de recursos y formatos. Para GUI pública, prueba de escritorio con teclado, ratón, cierre y controladores. |
| P2 · Bibliotecas especializadas | Web, persistencia y bases de datos, formatos de datos, redes, IA por interoperabilidad, videojuegos 2D, simulaciones, concurrencia, sistemas y dispositivos. Ampliar portabilidad y perfiles para esperanto e interlingua. | Gestión segura de recursos, módulos versionados, tipos y cadenas definidos, mediciones reales, portabilidad por plataforma. |
| P3 · Plataformas avanzadas | Compilación optimizada, WebAssembly, 3D, GPU, IDE y bibliotecas de electrónica o control especializado. | Semántica estable, validación de concurrencia, portabilidad y mediciones del intérprete de referencia. |

## Puertas de revisión

1. Confirmar los cambios de identidad, parser y consola en el corpus `.lat` y `.mict`. Revisar el contrato de memoria y sus límites antes de ampliar el recolector.
2. Reproducir la matriz Core–SDK con Debug, Release y los tres detectores. Comparar símbolos, un consumidor anterior, cargas y trazas.
3. Verificar el ZIP en Debian sin instalar en el sistema. Revisar versiones, licencias, comandos, ejemplos y rutas. La ventana experimental tiene su propia evidencia.
4. Una vez aceptado P0, estudiar cambios semánticos y módulos de P1 en propuestas separadas. Validar compatibilidad y rendimiento antes de comprometer la sintaxis de tipado gradual, clausuras o identificadores Unicode.

El objetivo de 1.0 es un lenguaje especificado y utilizable dentro de un alcance probado. La hoja de ruta ordena dependencias entre áreas y se actualiza cuando cambian la evidencia o las decisiones.

# Arquitectura de aplicaciones Mictlán P1

**Auditoría inicial · 13 de noviembre de 2026.** Core `66f8e2296a91f1b05ef680a720ddf145112965f1`, SDK `c44d03f605164a50e9a25a11d9407105b60827e7`, Lab `d239b6f487ef27546207c9ee05fcf2cd6c2b6745`. Las propuestas Core #5 y SDK #4 siguen abiertas en borrador. [Core #5](https://github.com/TuxMatic99/Mictlan-Core/pull/5) · [SDK #4](https://github.com/TuxMatic99/Mictlan-SDK/pull/4) · [Matriz Alpha](https://github.com/TuxMatic99/Mictlan-SDK/actions/runs/43384197638).

## Inventario y decisiones

| Componente | Comportamiento en la base | Decisión P1 |
| --- | --- | --- |
| `host_ui` | Una VM y una ventana 900 × 600 por sesión. Mantiene AST y programa. Registra UI, catálogo y gráficos. | Un solo anfitrión, con el alias de distribución `mictlan-ui`. Configuración de tamaño desde el programa y ciencia disponible por registro FFI. |
| `ui_runtime`, `ui_arbol`, `ui_layout_arbol` | Árbol acotado de 128 nodos, filas y columnas, posición compartida por dibujo e interacción. El layout reserva almacenamiento temporal cada cuadro. | Conservar el árbol y recalcular al cambiar el tamaño. Fijar la topología al abrir. Permitir retirar controles sin reutilizar el ID durante esa sesión. |
| Controles y entrada | Etiquetas, botones y campos UTF-8. El foco de Tab y los clics existen. Enter en un campo emite envío. | Mantener controles y navegación. Comprobar foco de ventana y devolver errores de validación legibles. |
| `ui_eventos`, `ui_despachador`, `ui_callbacks` | La cola contiene pares de tipo e ID y se procesa con presupuesto. El callback fijo es `__ui_despachar()`. | Asociaciones por ID y tipo con un nombre de función. Resolverlo en el contexto global al despachar. Conservar el callback histórico. Verificar ID activo al consumir la cola. |
| `ui_biblioteca` | Los IDs y modales del catálogo se activan explícitamente. El controlador no es genérico. | Conservar su registro y rutas históricas. El host nuevo no codifica IDs de VectorLab. |
| `graficos` | Círculos en píxeles, acotados a 128 comandos, dibujados después de la interfaz. | Añadir un lienzo opcional de líneas normalizadas con recorte, proporción cuadrada y capacidad fija. Conservar los círculos heredados. |
| Lab | El VectorLab publicado demuestra magnitudes en consola. El ejemplo gráfico abre una ventana separada. | Conservar los ejemplos. Implementar la aplicación gráfica y sus cálculos en Lab, usando los módulos del SDK. |
| Módulos | `incluir` de Alpha prueba primero las ubicaciones heredadas de `.lat`. Con extensión explícita selecciona el archivo; busca primero en el directorio de trabajo y luego junto al archivo actual. | Usar rutas con extensión explícita dentro del proyecto. Las tareas arrancan desde la raíz de la aplicación. Comprobar la carga también desde una carpeta limpia. |

## Propiedad y ciclo de vida

El host mantiene vivos la ruta, el AST y la función principal durante la sesión. Los callbacks se resuelven por nombre y sus descriptores prestados se usan solo dentro del despacho. El C de la interfaz copia textos, nombres y figuras en almacenamiento acotado. La cola guarda tipos e IDs por valor. Las cadenas devueltas por `ui.texto` pertenecen a Core y pueden quedar internadas hasta el cierre. Los recursos de ventana se cierran antes de retirar los registros FFI. Después se destruye el programa, la VM y finalmente el AST.

El callback anterior trataba todo error como VM comprometida. P0.2-E permite comprobar si la llamada protegida recuperó pila, contexto, contador de ejecución, manejador y límites de argumentos. Cuando un `LAT_ERRRUN` cumple esas condiciones, el host termina la sesión con código 1 y ejecuta la destrucción ordenada. Una inconsistencia estructural detiene el despacho y conserva la política de omitir el destructor de la VM comprometida. La comprobación no convierte un error de programa en éxito ni garantiza recuperar recursos que una extensión nativa hubiera abandonado.

El host mantiene el modo de memoria F de la Alpha. El contrato de G exige autorización de funciones nativas, raíces explícitas y puntos seguros. La API de GUI no depende de activar G. Las pruebas deben medir cuánto crece el uso con callbacks numéricos, resultados FFI de listas y textos variables. La recarga de un programa usa un proceso nuevo. El contrato P1 admite una ventana por proceso y deja la recarga en la misma VM para una revisión posterior.

## Aceptación prevista

Repetir la matriz Alpha e incorporar regresiones con Core, cola y callbacks reales bajo un backend de prueba para errores deterministas. Ejecutar también el anfitrión de producción con Raylib, X11 virtual y Mesa. Comprobar apertura, teclado, ratón, cambios de tamaño, cálculos, dibujo y cierre. Registrar por separado la comprobación en escritorio físico. La compilación de consola conserva sus dependencias de Core y Readline. La distribución gráfica añade Raylib y se comprueba fuera del árbol de compilación.

El anfitrión serializa entrada, despacho y renderizado en el hilo de la ventana. Una función interpretada larga puede impedir que el cuadro termine. El presupuesto del despachador opera entre eventos. Las API de ventana, teclado y texto siguen el contrato de Raylib 5.5. [Referencia de Raylib](https://www.raylib.com/cheatsheet/raylib_cheatsheet_v5.5.pdf).

# Mictlán UI 0.1 experimental

Ejecuta `host_ui -- mi_app.mict` desde la carpeta del proyecto. La distribución instala el mismo ejecutable como `mictlan-ui`. Acepta `.mict` y `.lat`. El archivo principal define la interfaz y sus acciones. El módulo `ciencia` está disponible en este anfitrión y en `mictlan-ciencia`.

```mictlan
ui.ventana("Mi aplicación", 760, 480)
ui.iniciar_columna(12)
    ui.etiqueta_id(10, "Pulsa el botón")
    ui.boton(1, "Saludar")
ui.fin_contenedor()

funcion saludar()
    mostrado = ui.poner_texto(10, "¡Hola desde Mictlán!")
fin
ui.al_evento(1, 1, "saludar")
```

El anfitrión ejecuta la carga inicial y abre una ventana por proceso. Para consultar su versión usa `--version`. Los programas con `ui.titulo` y `__ui_despachar()` pueden conservarlos.

## Ventana y controles

| Función | Contrato |
| --- | --- |
| `ui.ventana(titulo, ancho, alto)` | Configuración inicial. Dimensiones enteras entre 600 × 400 y 3840 × 2160. Predeterminado 900 × 600. |
| `ui.minimo(ancho, alto)` | Límite inferior de redimensionamiento entre 600 × 400 y el tamaño inicial. |
| `ui.titulo(titulo)` | Texto de la ventana. También puede actualizarlo un callback. |
| `ui.iniciar_fila(separacion)`, `ui.iniciar_columna(separacion)`, `ui.fin_contenedor()` | Un solo contenedor raíz. Separación finita en píxeles, de 0 a 3840. Las celdas se distribuyen proporcionalmente con pesos iguales. |
| `ui.etiqueta(texto)`, `ui.etiqueta_id(id, texto)`, `ui.boton(id, texto)`, `ui.campo_texto(id, inicial)` | Construcción inicial. IDs enteros únicos entre 0 y 9999. El árbol completo admite 128 nodos. Cada texto admite 255 bytes UTF-8. |
| `ui.texto(id)`, `ui.longitud_texto(id)` | Obtienen una cadena o número de puntos de código. Devuelven `falso` si el control no está disponible. |
| `ui.poner_texto(id, texto)` | Actualiza el valor y devuelve un lógico. El campo rechaza caracteres de control. |
| `ui.enfocar(id)`, `ui.habilitar(id, lógico)` | Cambian el foco o la disponibilidad de un control. Devuelven un lógico. |
| `ui.retirar(id)` | Oculta y deshabilita el control, borra su texto y sus asociaciones. Los eventos pendientes se descartan antes de llamar al script. Su celda se conserva y el ID queda reservado hasta cerrar. |
| `ui.cerrar()` | Solicita el cierre ordenado al terminar la acción actual. |

Las funciones de construcción, asociación y cierre se usan como instrucciones. **Guarda en una variable el resultado de las funciones que devuelven valores**, incluso si vas a descartarlo. Core puede conservar resultados sin consumir y el anfitrión exige una pila vacía al final de cada acción.

## Eventos

`ui.al_evento(id, tipo, "funcion_global")` asocia una acción sin parámetros. Usa `1` para botón por clic o Enter, `2` para Enter en un campo y `3` para Escape. Usa una cadena vacía para retirar la asociación. Las funciones deben existir cuando se registran. Las asociaciones se resuelven por nombre, por lo que el host no guarda descriptores prestados. Un evento sin asociación se entrega al callback histórico `__ui_despachar()` si existe. Dentro del callback, `ui_cb.id_actual()` y `ui_cb.tipo_actual()` describen el evento.

Tab y Mayús+Tab recorren los controles habilitados. Clic da foco al campo o activa un botón. Enter en un campo envía su valor, Retroceso borra un punto de código y Escape recupera el texto que tenía el campo al obtener el foco. Se admite entrada UTF-8. El repertorio visible depende de la fuente de Raylib. El redimensionamiento vuelve a calcular el layout y sus zonas de clic.

Un callback con error recuperable produce diagnóstico y cierra la aplicación con código 1, liberando la VM recuperada. Si los campos de pila o contexto quedan incoherentes, se cierran los recursos externos y se aísla la VM hasta terminar el proceso. El anfitrión es secuencial y conserva el modo de memoria de Alpha. Las cadenas que devuelve Core pueden quedar internadas hasta el cierre. La recarga se realiza cerrando y abriendo una nueva sesión. [Arquitectura](ARQUITECTURA.md).

## Gráfica y ciencia

`ui.lienzo(id)` reserva un panel de dibujo. `graficos.linea(x1, y1, x2, y2, r, g, b)` añade una línea de color con coordenadas en `[-1, 1]` y canales enteros en `[0, 255]`. El origen está en el centro y el eje Y sube. La escala en píxeles es igual para ambos ejes y se adapta al panel. Hay hasta 128 líneas. `graficos.limpiar()` borra círculos y líneas. Los círculos heredados se dibujan en píxeles. Todas estas funciones devuelven un lógico.

`ciencia.decimal(texto)` devuelve un número finito o `nulo`. Admite signo, punto decimal y exponente, con espacios y tabulaciones exteriores. Rechaza restos, hexadecimal, coma decimal, desbordamiento y subdesbordamiento indicado por el analizador de C. La aplicación elige sus límites físicos o científicos adicionales. `ciencia.longitud2`, `ciencia.producto_punto2` y `ciencia.sumar2` conservan su contrato.

## Proyecto

Usa `principal.mict` y una carpeta `modulos/`. El módulo exporta sus funciones con `global funcion`. `incluir("modulos/nombre.mict")` busca primero en el directorio de trabajo, luego junto al archivo actual y por último en `LATINO_LIB`. Usa la raíz del proyecto como directorio de trabajo y nombres únicos. La extensión explícita evita elegir por accidente un `.lat` del mismo nombre.

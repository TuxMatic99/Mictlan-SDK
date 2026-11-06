# Mictlán SDK: estado del desarrollo

Fecha: 5 de noviembre de 2026
Etapa: Mictlán Alfa 0.1

## Origen

Proyecto derivado de LatinoVox, licencia MIT.

Revisión base de SDK:
ba09c5c5879717d06436c6dd55a9e9f30e0f5f6a

Rama:
desarrollo/mictlan-alpha

Núcleo utilizado:
mictlan-core, commit 3713cd2

## Compilación

Sistema: Debian GNU/Linux x86_64
Compilador: GCC 14.2.0
CMake: 3.31.6
Biblioteca gráfica: Raylib 6.5-dev

Resultado: compilación Debug correcta.

## Pruebas automatizadas

CTest: 24/24 pruebas aprobadas.
Tiempo observado: 0,49 segundos.


## Hito: biblioteca de dibujo 2D

Fecha: 6 de noviembre de 2026

Estado: implementación inicial aprobada.

### Resultados

- Biblioteca mictlan_dibujo2d compilada.
- Registro de círculos implementado.
- Validación de coordenadas y radio implementada.
- Capacidad inicial: 128 círculos.
- Prueba mictlan_dibujo2d_basico aprobada.
- Suite completa del SDK: 24/24 pruebas aprobadas.
- Tiempo observado de CTest: 0,45 segundos.

### Pendientes

- Renderizar los círculos mediante Raylib.
- Integrar la biblioteca con host_ui.
- Exponer funciones gráficas mediante FFI.
- Dibujar figuras desde Mictlán Lab.
- Realizar pruebas de memoria y gráficos.

## Prueba gráfica real

Aplicación:
ejemplos/mi_primera_ventana.lat

Resultados:

- Ventana abierta correctamente.
- OpenGL 4.6 inicializado.
- GPU Intel UHD Graphics 620 detectada.
- Botón Saludar funcional.
- Botón Despedirse funcional.
- Eventos recibidos por el intérprete.
- Actualización de etiquetas comprobada.
- Ventana cerrada correctamente.

## Limitaciones

- El ejecutable gráfico todavía se llama host_ui.
- Algunas funciones internas conservan nombres LatinoUI.
- Se utiliza liblatino.so por compatibilidad.
- No existe instalador público de Mictlán SDK.
- No se ha validado todavía una instalación limpia.
- Queda pendiente la validación instrumentada completa.
- Las pruebas no garantizan ausencia total de defectos.

## Próximos objetivos

1. Registrar la primera aplicación gráfica en Git.
2. Definir el comando público mictlan-ui.
3. Crear una estructura instalable y reutilizable.
4. Documentar las funciones públicas del SDK.
5. Ejecutar pruebas de memoria y compatibilidad.
6. Publicar una versión alfa para usuarios.
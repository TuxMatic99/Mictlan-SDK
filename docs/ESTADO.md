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



## Hito: primer renderizador gráfico 2D

Fecha: 6 de noviembre de 2026

Estado: demostración visual aprobada.

### Resultados

- Biblioteca mictlan_dibujo2d compilada.
- Backend mictlan_render_raylib compilado.
- Demostración demo_mictlan_dibujo2d compilada.
- Círculo naranja renderizado en una ventana real.
- OpenGL 4.6 inicializado correctamente.
- Recursos gráficos liberados al cerrar.
- 24 de 24 pruebas automatizadas aprobadas.
- Tiempo total de CTest: 1,66 segundos.

### Pendientes

- Conectar el renderizador con host_ui.
- Exponer la API gráfica mediante FFI.
- Dibujar círculos desde archivos .lat.
- Añadir pruebas automatizadas de la integración.
- Comprobar memoria mediante sanitizadores.


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
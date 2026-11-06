# Informe de avance 02: Del lenguaje al píxel

**Proyecto:** Mictlán  
**Fecha:** 6 de noviembre de 2026  
**Etapa:** Desarrollo de Mictlán Alfa 0.1  
**Hito:** Primera figura dibujada desde un programa Mictlán.

## 1. Resumen ejecutivo

Mictlán ha logrado ejecutar una función gráfica propia desde un programa escrito en su lenguaje.

La función `graficos.circulo()` comunica el intérprete con una biblioteca desarrollada en C mediante FFI. La biblioteca valida los parámetros, almacena los datos geométricos y permite que el renderizador Raylib dibuje la figura en pantalla.

El resultado fue comprobado utilizando Mictlán Lab.

## 2. Resultados verificados

| Componente | Resultado |
|---|---|
| Intérprete Mictlán | Funcional |
| Registro del módulo `graficos` | Correcto |
| Función `graficos.circulo()` | Funcional |
| Biblioteca de círculos | Funcional |
| Renderizador Raylib | Funcional |
| Círculo visible desde `.lat` | Confirmado |
| Botones y callbacks | Funcionando |
| Cierre de ventana | Correcto |
| Pruebas automatizadas del SDK | 24/24 aprobadas |

## 3. Arquitectura implementada

La cadena de ejecución es:

Mictlán Lab → FFI → Mictlán Dibujo 2D → Raylib → OpenGL.

El programa utiliza la siguiente instrucción:

```python
graficos.circulo(680, 360, 45, 230, 110, 60)
```

La operación crea un círculo con posición, radio y color especificados por el usuario.

La implementación permite utilizar la biblioteca gráfica sin introducir funciones específicas de Mictlán Lab dentro del núcleo del lenguaje.

## 4. Problemas resueltos

Durante la integración se presentaron errores de enlazado en dos ejecutables de pruebas históricas.

Se identificó que dichas pruebas incluían directamente el código de `host_ui.c` y necesitaban dependencias adicionales.

La configuración de CMake fue corregida para permitir que esos ejecutables utilizaran la biblioteca de almacenamiento sin requerir el renderizador real.

Después de la modificación, las 24 pruebas del SDK volvieron a aprobarse.

## 5. Limitaciones actuales

La API gráfica todavía es experimental.

El sistema dispone de una operación para registrar círculos, pero no incluye una interfaz completa de primitivas gráficas.

El lienzo tiene una capacidad fija de 128 círculos.

La conexión FFI está implementada provisionalmente dentro de `host_ui.c`.

La nueva función gráfica todavía carece de una prueba de integración automatizada propia.

No se ha completado una auditoría de memoria de esta nueva integración.

## 6. Próximo objetivo

Crear una prueba automatizada para `graficos.circulo()` que compruebe argumentos válidos, valores inválidos y límites de capacidad.

Posteriormente, separar la FFI del host principal y ampliar la biblioteca con otras primitivas gráficas.

## 7. Conclusión

Mictlán ha alcanzado una capacidad nueva: ejecutar instrucciones gráficas desde su propio lenguaje y representar el resultado en una ventana real.

**El próximo hito será asegurar y modularizar esta primera API gráfica.**
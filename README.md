# Mictlán SDK

Bibliotecas, herramientas y ejemplos para el lenguaje Mictlán. El SDK usa la API de [Mictlán Core](https://github.com/TuxMatic99/Mictlan-Core). Sus módulos se integran mediante funciones de C registradas para los programas Mictlán.

## Empezar con la Alpha de consola

La [guía de instalación](docs/alpha/INSTALAR.md) explica cómo extraer el paquete de Debian, escribir un archivo `.mict`, usar VS Code y ejecutar ejemplos de ciencia. El ejecutor científico registra `ciencia.longitud2`, `ciencia.producto_punto2` y `ciencia.sumar2`. Los programas `.lat` compatibles se ejecutan con el mismo Core.

## Compilar y comprobar

Sigue la [reproducción en Debian](docs/alpha/REPRODUCIR.md) para compilar el Core y el SDK exactos, ejecutar CTest, comprobar memoria y generar el ZIP. La matriz conserva resultados de Debug, Release y ASan, UBSan y LSan. La [hoja de ruta](docs/alpha/HOJA_DE_RUTA.md) identifica las prioridades posteriores.

## Aplicación gráfica experimental

El SDK compila `host_ui` con Raylib. Desde una sesión gráfica, puedes probar:

```bash
./ruta/al/build/sdk/host_ui ejemplos/mi_primera_ventana.lat
```

Pulsa **Enter** para saludar, luego **Tab** y **Enter** para cambiar de botón y activar el segundo evento. Cierra la ventana desde el gestor. Puedes copiar el programa a un archivo `.mict` y editar su texto y acciones. El ZIP de consola contiene el ejemplo. Para ejecutarlo con ventana se necesita compilar el anfitrión gráfico. Consulta [host UI](docs/host-ui.md).

## Origen y licencia

Mictlán SDK se desarrolló a partir de LatinoVox 2D. Conserva su [documentación histórica](docs/historia/README_LATINOVOX.md) y el historial de contribuciones. Los módulos distribuidos se rigen por [LICENSE](LICENSE) y por los avisos de sus dependencias.

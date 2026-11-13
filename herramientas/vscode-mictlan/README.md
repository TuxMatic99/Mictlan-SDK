# Mictlán: soporte visual de archivos `.mict` para VS Code

Identifica los archivos `.mict` como lenguaje **Mictlán**, ofrece un ícono original para temas claros y oscuros, y añade un resaltado básico. La versión de la extensión aparece en `package.json`.

El símbolo combina un cráneo geométrico inspirado en el signo *Miquiztli* con una M escalonada y nueve elementos de corona. Es una **interpretación contemporánea**, no una reproducción exacta de un glifo histórico.

## Instalación local (VS Code en Linux)

El instalador usa Python 3 para leer el manifiesto. Desde el directorio de la extensión, ejecuta:

```bash
bash instalar-vscode.sh
```

El instalador copia la extensión al directorio de extensiones de VS Code del usuario, sin usar `sudo`. Puedes indicar un directorio alternativo con `MICTLAN_VSCODE_EXTENSIONS_DIR`. Después, en VS Code, ejecuta **Ctrl + Shift + P** > **Developer: Reload Window** (o reinicia VS Code).

Abrir un archivo `.mict`, por ejemplo `mictlan-lab/pruebas/primer_experimento.mict`. Debe aparecer «Mictlán» como modo de lenguaje. Si el tema de íconos admite íconos propios de lenguajes, se mostrará el símbolo del archivo.

El paquete Alpha trae un proyecto de ejemplo con una tarea **Mictlán ejecutar archivo activo**. Abre el proyecto y selecciona la tarea desde **Terminal > Ejecutar tarea**. En un proyecto que use programas `.lat`, puedes elegir el modo Mictlán para un archivo o añadir `"files.associations": {"*.lat": "mictlan"}` a su configuración local.

**Importante:** algunos temas de íconos reemplazan los iconos de las extensiones; otros los ocultan. Prueba **Preferences: File Icon Theme > Seti (Visual Studio Code)** si el ícono no se ve. Esta extensión *no sustituye* el tema de íconos general para no afectar los archivos Python, C, JavaScript, etc.

## Desinstalación local

```bash
bash desinstalar-vscode.sh
```

Luego recargar la ventana. La desinstalación borra solamente esta extensión local.

## Registro de ícono en Linux (opcional)

Los iconos de archivos que muestra el gestor de archivos (GNOME Files, Dolphin, etc.) son independientes de los de VS Code. Para registrar `.mict` como MIME de usuario, sin usar sudo:

```bash
bash linux/instalar-mime.sh
```

Dependiendo del escritorio y del tema de íconos, podría ser necesario cerrar sesión o reiniciar el gestor de archivos. El registro MIME no instala ni modifica el intérprete.

## Límites y siguientes pasos

- Este paquete **no incorpora** compilador, intérprete, servidor de lenguaje (LSP), depurador o ejecución desde VS Code.
- El resaltado de sintaxis es preliminar; puede ajustarse cuando congelemos la gramática de Mictlán.
- Se asocia solamente `.mict`, no `.lat`, para no apropiarse de archivos del lenguaje Latino.
- Los recursos `icons/` son PNG transparentes derivados de un diseño original del proyecto.
- Para JetBrains, Eclipse, NeoVim u otros IDE se requieren integraciones independientes.

El proyecto puede conservarse en `mictlan-sdk/herramientas/vscode-mictlan` y versionarse por separado del Core.

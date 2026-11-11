# Mictlán: documento de relevo para continuar en otra conversación

**Fecha:** 7 de noviembre de 2026.  
**Alcance:** hechos respaldados por salidas de terminal compartidas durante el desarrollo y revisión del GitHub conectado. Los estados locales pueden haber cambiado después de esas salidas.

## Visión del proyecto

Desarrollar **Mictlán**, lenguaje de programación de propósito general con sintaxis accesible en español, derivado del lenguaje Latino, pero con identidad y evolución propias. Metas de largo plazo: investigación científica, cálculo matemático, visualización, interfaces gráficas, inteligencia artificial, interoperabilidad, uso en equipos modestos, instalación y desinstalación sencillas y soporte multiplataforma. No confundir metas futuras con capacidades ya terminadas. Mantener atribuciones y licencias MIT correspondientes al código heredado.

## Estructura local actual

Carpeta de trabajo principal: `~/Proyectos/Mictlan/`.

| Repositorio local | Función | Rama observada |
|---|---|---|
| `mictlan-core/` | Intérprete/VM de Latino adaptado a Mictlán, extensiones `.mict` y `.lat`, herramientas de empaquetado | `desarrollo/mictlan-alpha` |
| `mictlan-sdk/` | Bibliotecas gráficas y científicas, host UI, FFI y pruebas, herramienta de VS Code | `desarrollo/mictlan-alpha` |
| `mictlan-lab/` | Programas de ejemplo, pruebas y laboratorios para usuarios de Mictlán | `main` |

Fuera de esos repositorios: `build-core-debug/`, `build-core-release/`, `build-sdk-debug/`, `build-deb-local/`, `artefactos/`. No subir carpetas de compilación al repositorio salvo justificación explícita.

## Hitos confirmados en terminal

- Core: `.mict` admitido y `.lat` conservado; los archivos incorrectos o inexistentes retornan código de error `1`. Prueba de regresión `MICTLAN_EXTENSIONES_OK` para cinco escenarios. Último commit de Core mostrado: `b3be302` (`test(core): proteger extensiones mict y lat`).
- Distribución Core: paquete portable mínimo, empaquetado automatizado, `.deb` experimental para Debian amd64, `lintian --fail-on error,warning` sin problemas observados y ejecución del archivo `.lat` desde paquete extraído. Esto **no** prueba portabilidad universal ni instalación real en todas las distribuciones.
- SDK: arquitectura gráfica separada y puente FFI; integración raylib y host. Biblioteca científica `MictlanVector2` en C con operaciones de suma, escalar, producto punto, longitud y normalización.
- SDK: ejecutor `build-sdk-debug/mictlan_ciencia_consola` ejecuta programas `.mict` con módulo `ciencia`. Se han probado `ciencia.longitud2` (3,4 → 5) y producto punto ((3,4)·(5,12) → 63; perpendicular → 0).
- La suite SDK alcanzó **28/28 pruebas aprobadas** según la última salida de CTest compartida sobre ese hito. Último commit SDK explícitamente mostrado después de ello: `4648f8d` (`docs(progress): registrar informe 04 de Mictlan`).
- Lab: `aplicacion/vectorlab.mict` imprimió longitudes 5 y 13. `pruebas/producto_punto.mict` imprimió 63 y 0. Prueba `vectorlab_03.mict` mostró suma (8,16) y escalamiento (6,8). Último commit Lab compartido: `8a5233b` (`feat(lab): validar producto punto desde Mictlan`).
- Identidad: extensión `.mict`, iconos visibles en VS Code y gestor de archivos Debian, MIME `text/x-mictlan`, extensión VS Code `tuxmatic.mictlan-language@0.1.0`, sintaxis básica y tareas locales.

## Trabajo actual pendiente de cerrar

- Se añadió a `mictlan-sdk/src/ciencia/mictlan_ciencia_ffi.c` una función de suma vectorial `ciencia.sumar2(ax,ay,bx,by)`, con devolución de las componentes como lista (`[x,y]`). **La compilación del ejecutor científico sí finalizó**, pero en el último mensaje aún no se mostró la ejecución directa y validada de `mictlan-lab/pruebas/suma_vectorial.mict`.
- Hubo un fallo de VS Code al utilizar `Ctrl+Shift+B` desde la ventana de SDK; lanzó una tarea antigua `cmake --build build --parallel && ./build/motor` y falló porque `mictlan-sdk/build` no existe. No indica error en C. Se sugirió una configuración global de VS Code `Mictlan.code-workspace`, pero **no hay constancia aún de que se haya instalado y probado**.
- Falta crear prueba automatizada específica para `ciencia.sumar2`, integrar multiplicación escalar como FFI, verificar casos límite y guardar commits cuando esté validado.
- Informes del SDK: `docs/informes/2026-11-07_04_Informe_de_progreso_Mictlan.md` confirmado en Git. Un documento más antiguo `docs/informes/2026-11-06_03_Mictlan_sale_del_laboratorio.md` figuraba como sin seguimiento; revisar antes de decidir qué hacer con él.
- Archivos locales como `mictlan-lab/pruebas/hola_mictlan.mict` aparecían sin seguimiento. No borrar ni añadir indiscriminadamente.

## GitHub conectado e investigación

Cuenta GitHub confirmada: **TuxMatic99**. Repositorios existentes comprobados:

- `https://github.com/TuxMatic99/LatinoVox`: aplicación/sandbox 2D con C, Raylib y Latino; no es un repositorio del nuevo lenguaje. Último commit en GitHub observado `58f183aa...` (24 de octubre de 2026, versión 0.8.0).
- `https://github.com/TuxMatic99/latino-Core`: repositorio público distinto al `mictlan-core` local; comprobar remotos e historiales antes de enlazar cualquier cosa.

Se recomendó publicar **repositorios nuevos separados** `Mictlan-Core`, `Mictlan-SDK`, `Mictlan-Lab` para preservar las tres historias Git locales y dejar LatinoVox intacto. Antes de subir, ejecutar `git remote -v`, `git status --short --branch` y `git log -1 --oneline` en cada carpeta. Verificar no incluir secretos ni artefactos de compilación. **No se han creado estos repositorios ni subido el código desde esta conversación.**

## GitHub Linguist y el lenguaje Mictlán

Las estadísticas de lenguajes de GitHub usan **GitHub Linguist**. Cambiar extensiones o poner `*.mict linguist-language=Mictlan` no registra por sí solo un lenguaje nuevo; Linguist debe conocerlo. Para reconocimiento oficial harían falta registro en `languages.yml`, gramática, muestras reales y satisfacer criterios de uso público del proyecto Linguist. Es una meta a largo plazo, no un requisito para publicar Mictlán ahora.

Fuentes:
- https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-repository-languages
- https://github.com/github-linguist/linguist/blob/main/CONTRIBUTING.md
- https://github.com/github-linguist/linguist/blob/main/docs/overrides.md
- https://docs.github.com/en/migrations/importing-source-code/using-the-command-line-to-import-source-code/adding-locally-hosted-code-to-github

## Normas acordadas para continuar

1. Explicar cada comando para un usuario que está aprendiendo C, Git, CMake y VS Code.
2. Una función o módulo principal por etapa, sin alternar continuamente entre Core, SDK, Lab, gráficos e instaladores.
3. Cada cambio: edición pequeña → compilación → prueba específica → suite completa → `git diff --check` → commit explícito.
4. Antes de cambiar archivos, recuperar el estado real con salidas de terminal o leer el código publicado en GitHub. No inferir que el estado de los archivos corresponde exactamente a una salida antigua.
5. Proteger la licencia MIT del núcleo heredado y atribuciones de terceros.
6. Evitar `git push --force`, `git reset --hard`, `rm -rf`, o cambiar remotos sin revisar su estado.

## Primera tarea propuesta para el nuevo chat

**Publicar sin riesgo los tres repositorios locales en repositorios nuevos de GitHub, conservando historia y ramas.** Primero solicitar/analizar resultados de estas verificaciones de solo lectura:

```bash
cd ~/Proyectos/Mictlan
for repo in mictlan-core mictlan-sdk mictlan-lab; do
  echo "===== $repo ====="
  git -C "$repo" status --short --branch
  git -C "$repo" remote -v
  git -C "$repo" log -1 --oneline
done
```

Posteriormente revisar nuevos repositorios vacíos, autenticación y ejecutar `git push` de la rama correcta por separado. No sobrescribir ni reutilizar el repositorio LatinoVox.

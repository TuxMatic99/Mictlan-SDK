# P0.2-F: reproducir el contrato Core-SDK en Debian

Fecha: 12 de noviembre de 2026. La rama `verificacion/p02f-ci` amplia la
automatizacion de `verificacion/p03-3-ci` (`1f666360aac32ffc74f27e6e2ce10a6e6bb065de`).
No cambia las funciones del SDK ni los 65 casos de sus verificadores.

## Que se compara

Un SHA es la identificacion exacta de una version. El archivo
`ci/p03/contrato.json` fija los SHA de Core y Raylib y el numero esperado de
pruebas; el programa rechaza fuentes modificadas o versiones distintas.

| Nombre | Core exacto | Proposito |
| --- | --- | --- |
| p02f_base | 651b27aa4adeffd3f116841fc9a24c4cd74cf842 | Regresiones previas al arreglo; conserva fallos reproducibles |
| p02f_owner | 52317c21f2cb9b608796b4075bb6bf2c109ab327 | Primer arreglo de propiedad; ejecucion historica conservada |
| p02f | 0699dabeca9498a1165472c9569634e86bc8d32b | Propiedad y proteccion al clonar ciclos/profundidad |
| p02f_e | 7d6e45ecf432a475d6898f66a4abde2e4c0ec821 | Experimento separado con el parche de pila P0.2-E |

La matriz ejecuta base, F y F+E en Debug, Release y sanitizadores. Estos ultimos
usan ASan y UBSan juntos, con LSan integrado activo al terminar el proceso.
Tambien se comprueba LSan independiente mediante un programa limpio y otro con
una fuga deliberada de 137 bytes. Los controles ASan/UBSan deben detectar errores
reales. No basta con que una opcion figure escrita en CMake.

Se conservan 32 pruebas SDK, 65 del verificador, cuatro secuencias de VM,
cuatro contratos de identidad/alias, el inventario completo Core, cinco pruebas
de extensiones y, en el perfil instrumentado, doce regresiones modulares.
La base falla deliberadamente como evidencia comparativa: no se usa WILL_FAIL,
continue-on-error ni una lista de excepciones para convertirla en exito.

## Preparar una copia independiente

Estos comandos crean carpetas nuevas; no cambian tus repositorios habituales.
Ejecutarlos en una terminal normal, fuera de gdb, strace u otro trazador.
En Debian se necesitan las herramientas de compilacion y las bibliotecas
de desarrollo para Readline y Raylib:

```sh
sudo apt update
sudo apt install build-essential cmake python3 git binutils pkg-config \
    libreadline-dev xorg-dev libgl1-mesa-dev

experimento=$(mktemp -d "$PWD/mictlan-p02f-XXXXXXXX")
cd "$experimento"
git clone --branch verificacion/p02f-ci --single-branch \
    https://github.com/TuxMatic99/Mictlan-SDK.git sdk
git clone --no-checkout https://github.com/TuxMatic99/Mictlan-Core.git core
git clone --no-checkout https://github.com/raysan5/raylib.git raylib
```

Para repetir exactamente un informe, usar su SHA completo del SDK con
`git -C sdk checkout --detach SHA_DEL_INFORME` antes del siguiente bloque.
Sin ese paso se prueba la revision publicada actualmente en la rama, cuyo SHA
se registra igualmente. Seleccionar una fila de la tabla, por ejemplo F+E:

```sh
revision=p02f_e
core_sha=$(python3 -c 'import json,sys; print(json.load(open("sdk/ci/p03/contrato.json"))["core_revisions"][sys.argv[1]]["sha"])' "$revision")
raylib_sha=$(python3 -c 'import json; print(json.load(open("sdk/ci/p03/contrato.json"))["raylib_sha"])')
sdk_sha=$(git -C sdk rev-parse HEAD)
git -C core checkout --detach "$core_sha"
git -C raylib checkout --detach "$raylib_sha"
printf 'SDK=%s\nCore=%s\nRaylib=%s\n' "$sdk_sha" "$core_sha" "$raylib_sha"
```

## Compilar y comprobar

Cada perfil debe usar una carpeta de salida que todavia no exista. El siguiente
comando compila todo y produce evidencias incluso cuando las pruebas fallan:

```sh
perfil=sanitizers
bash sdk/scripts/p03/preparar_ci.sh "$perfil" "$PWD/core" "$PWD/raylib" \
    "$PWD/resultados-$revision-$perfil" "$sdk_sha" "$revision"
```

Repetir cambiando `perfil=debug` y despues `perfil=release`. Si se interrumpe una
compilacion, conservar sus archivos y escoger otro nombre de salida al repetir.
Los directorios de resultados no deben estar dentro de los repositorios.

El comando puede devolver error porque la bateria contiene fallos conocidos.
Eso no implica que todas las pruebas hayan fallado. Para ver el resumen:

```sh
python3 -m json.tool "resultados-$revision-$perfil/evidence/report.json"
```

`checks` separa las familias; cada caso conserva su resultado. `commands` incluye
comandos, codigos de salida y nombres de trazas. Tambien hay JUnit, versiones,
opciones CMake, huellas de archivos y comprobacion de simbolos/layout de la ABI
(la forma en que Core y SDK intercambian datos en memoria).

## Interpretar sin ocultar problemas

- PASS: el caso cumplio sus condiciones. En memoria requiere ademas que los
  controles de sanitizadores funcionen y no aparezcan informes de errores.
- FAIL: el programa, su configuracion o su contrato falla. Un fallo conocido
  sigue contando como fallo. `coverage` tiene una entrada ausente; F sin E
  conserva el fallo de pila. La base conserva las fugas anteriores.
- BLOCKED_INFRASTRUCTURE: no fue posible comprobarlo, por ejemplo porque LSan
  no puede inspeccionar procesos bajo ptrace. No equivale a ausencia de fugas.

El entorno estricto no utiliza supresiones, detect_leaks=0 ni LSAN exitcode=0.
Los verificadores rechazan ASan/UBSan/LSan aunque coincidan la salida y el mensaje
del error funcional esperado. El clasificador da prioridad a un error real del
programa si tambien aparece un bloqueo de infraestructura.

GitHub Actions usa `ubuntu-24.04` sin depurador ni trazador. Las ejecuciones
[43164505980](https://github.com/TuxMatic99/Mictlan-SDK/actions/runs/43164505980)
y [43166246005](https://github.com/TuxMatic99/Mictlan-SDK/actions/runs/43166246005)
ya comprobaron los controles LSan reales y la transicion de las fugas
0/200/264/528 a cero fugas detectadas; SDK paso de 30/32 a 32/32 instrumentadas.
La ejecucion final vuelve a comprobar F y F+E, sin extrapolar resultados.
Descargar los artefactos desde la ejecucion: su retencion configurada es 14 dias.

## Limites que requieren revision

F conserva contenidos de listas y diccionarios hasta cerrar la VM. Es una
propiedad por region: resuelve el cierre y protege alias, pero no es recoleccion
de basura durante la ejecucion. Una VM larga puede acumular objetos sustituidos.
No se permite liberar directamente con `free` objetos administrados ni prestar
contenidos entre VM distintas. Los punteros C externos, clases e instancias
necesitan contratos adicionales. Los experimentos no certifican todas las
posibles rutas del lenguaje, la falta de memoria ni otras plataformas/ABI.

Las PR son borradores para revision. Ninguno de estos comandos fusiona ramas.

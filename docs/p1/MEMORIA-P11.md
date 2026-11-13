# Memoria gráfica experimental

P1.1 conserva el modo habitual de la Alpha. Para una sesión de prueba, ejecuta:

```bash
MICTLAN_UI_METRICAS=1 mictlan-ui --gc-experimental -- principal.mict
```

Usa la biblioteca de Core y las cabeceras de la misma revisión P1.1. Sin el argumento se usa el modo anterior. La consola y programas C que usen solo `latG_habilitar` conservan la duración anterior de las cadenas internadas.

| Referencia | Contrato |
| --- | --- |
| Pila y contextos | Core traza las celdas activas y los contextos. El anfitrión comprueba que al salir del despacho la pila está vacía y el contexto es global. |
| Callback | El anfitrión copia el nombre del callback. Busca su función global solo para el evento en curso. |
| Campos, títulos, cola y dibujo | Los textos se copian a buffers C. La cola guarda tipo e ID. El plano conserva coordenadas y colores. |
| Resultado científico | La pila y los contenedores mantienen los objetos. C conserva escalares sin volver a acceder a celdas desapiladas. |
| AST, rutas y funciones | El AST principal permanece vivo hasta el cierre. Core conserva funciones, constantes y rutas de origen compiladas. |
| Listas, diccionarios y ciclos | Core recorre los recursos alcanzables por identidad. Una referencia desconocida impide el barrido. |
| Código C que retenga objetos | Copia el texto o fija `getCadena`, el objeto o el contenedor registrado. Libera esa fijación tras el último uso. |
| Ventana y recursos gráficos | Pertenecen a Raylib o al anfitrión. Se cierran antes de destruir la VM. |

El anfitrión autoriza por dirección las funciones comprobadas antes del script inicial. Incluye `ui`, `ui_cb`, gráficos, ciencia y un conjunto acotado de Core. El código de `incluir` conserva rutas de origen para el bytecode. La carga de código nativo inhibe la recolección antes de llamar a sus inicializadores. Una función ajena a la lista autorizada, como `escribir` o las operaciones de la biblioteca de catálogo, cambia la VM a retención conservadora. El siguiente intento de recolectar deja un diagnóstico y suspende los barridos de esa sesión.

Tras iniciar y después del despacho se recolecta cuando transcurren 128 eventos o la VM contabiliza 2 MiB adicionales desde el último barrido. Cada punto comprueba que el callback terminó y que la VM está en reposo. Las pausas son síncronas. Un error recuperable conserva la política de cierre de P1. La prueba de pila de Core reutiliza una VM fuera de la interfaz después de errores de tipo y rango. Si la VM pierde sus invariantes, se desconectan los recursos externos y se conserva el aislamiento al terminar el proceso.

Las métricas registran bytes actuales y pico de Core, RSS y pico de proceso en Linux, cadenas internadas, reservas y bytes recuperados acumulados, y duración total y máxima de los barridos exitosos. Una reserva es una entrada del registro e incluye descriptores, contenedores, cubetas y cadenas según el caso. El pico de Core puede incluir el buffer temporal del compilador. El asignador, las bibliotecas y el renderizado también cuentan en RSS.

El anfitrión mantiene una VM y una ventana por proceso. La compilación repetida sigue reteniendo bytecode y constantes. Una aplicación que guarde un historial ilimitado mantiene alcanzables sus datos. Las clases, recursos externos y carga nativa siguen los límites de G. Los ensayos de 100.000 eventos utilizan el despacho real con entrada y pantalla deterministas. El perfil de X11 verifica por separado la entrada y el cierre de ambas aplicaciones.

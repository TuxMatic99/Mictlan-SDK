#ifndef _POSIX_C_SOURCE
#define _POSIX_C_SOURCE 200809L
#endif
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "raylib.h"
#include "latino.h"
#include "latast.h"
#include "latmv.h"
#include "latobj.h"
#if defined(__has_include)
#if __has_include("latmemoria.h")
#include "latmemoria.h"
#endif
#endif
#if defined(__has_include)
#if __has_include("mictlan_version.h")
#include "mictlan_version.h"
#endif
#endif
#ifndef MICTLAN_VERSION
#define MICTLAN_VERSION "experimental"
#endif
#include "mictlan_ciencia_ffi.h"
#include "ui_runtime.h"
#include "ui_utf8.h"
#include "ui_eventos.h"
#include "ui_callbacks.h"
#include "ui_despachador.h"
#include "ui_biblioteca.h"
#include "mictlan_dibujo2d.h"
#include "mictlan_graficos_ffi.h"

#ifndef MICTLAN_HOST_PRUEBAS
#include "mictlan_render_raylib.h"
#endif
#ifdef __linux__
#include <sys/resource.h>
#include <unistd.h>
#endif

static UIRuntime ui;
static MictlanLienzo lienzo_graficos;
static MictlanPlano plano_graficos;
static int siguiente_etiqueta;
static struct {
    bool configurada, cerrar;
    int ancho, alto, minimo_ancho, minimo_alto, lienzo_id;
    bool retirado[LUI_MAX_NODOS];
    char acciones[LUI_MAX_NODOS][UI_EVENTO_CANCELAR][MAX_ID_LENGTH];
} sesion;

typedef struct {
    UICBContexto *callbacks;
    int ultimo_clic;
} HostEventos;

typedef struct {
    bool activo;
    int estado;
    size_t recolecciones, reservas, bytes, ultimo_evento, bytes_base;
    double total_ms, max_ms;
} HostMemoria;

#ifdef LAT_G_CADENAS_EXPLICITAS
enum { GC_EVENTOS = 128, GC_CRECIMIENTO_BYTES = 2 * 1024 * 1024 };
static bool autorizar_modulo(lat_mv *mv, const char *modulo, const char *const *nombres)
{
    lat_objeto *base = mv->contexto[0];
    hash_map *tabla = NULL;
    if (modulo) {
        lat_objeto *obj = latO_obtener_contexto(mv, base, modulo);
        if (!obj || obj->tipo != T_DIC) return false;
        tabla = getDic(obj);
    }
    for (; *nombres; ++nombres) {
        lat_objeto *func = tabla ? latH_obtener(tabla, *nombres)
                                 : latO_obtener_contexto(mv, base, *nombres);
        if (!func || func->tipo != T_CFUN || latG_autorizar(mv, getCfun(func)) != LAT_G_OK)
            return false;
    }
    return true;
}

static bool habilitar_memoria(HostMemoria *memoria, lat_mv *mv)
{
    /* Resolver funciones antes del primer script. Un nombre de usuario
       nunca puede ampliar la lista de direcciones auditadas. */
    if (latG_habilitar(mv) != LAT_G_OK || latG_habilitar_cadenas(mv) != LAT_G_OK ||
        !autorizar_modulo(mv, NULL, (const char *const[]){"incluir", "tipo", "error", NULL}) ||
        !autorizar_modulo(mv, "cadena", (const char *const[]){"longitud", "formato", "separar", NULL}) ||
        !autorizar_modulo(mv, "lista", (const char *const[]){"longitud", NULL}) ||
        !autorizar_modulo(mv, "archivo", (const char *const[]){"leer_texto_seguro", "escribir_atomico", NULL}) ||
        !autorizar_modulo(mv, "ciencia", (const char *const[]){"decimal", "sumar2", "longitud2", "producto_punto2", NULL}) ||
        !autorizar_modulo(mv, "graficos", (const char *const[]){"circulo", "limpiar", "linea", NULL}) ||
        !autorizar_modulo(mv, "ui_cb", (const char *const[]){"id_actual", "tipo_actual", NULL}))
        return false;
    memoria->activo = true;
    memoria->estado = LAT_G_OK;
    return true;
}

static void recolectar_memoria(HostMemoria *memoria, const UICBContexto *cb, size_t eventos)
{
    if (!memoria->activo || cb->ejecutando || cb->inutilizada || !ui_cb_vm_en_reposo(cb->mv))
        return;
    double inicio = 0, fin = 0;
    (void)ui_despachador_reloj_monotonico(NULL, &inicio);
    memoria->estado = latG_recolectar(cb->mv);
    (void)ui_despachador_reloj_monotonico(NULL, &fin);
    if (memoria->estado != LAT_G_OK) {
        memoria->activo = false;
        fprintf(stderr, "Mictlán UI: recolección suspendida (%d). La VM conserva sus reservas hasta el cierre.\n",
                memoria->estado);
        return;
    }
    latG_medicion medicion = {0};
    (void)latG_medir(cb->mv, &medicion);
    memoria->ultimo_evento = eventos;
    memoria->bytes_base = medicion.bytes_vm;
    memoria->recolecciones++;
    memoria->reservas += medicion.reservas_recuperadas;
    memoria->bytes += medicion.bytes_recuperados;
    double pausa = fin >= inicio ? fin - inicio : 0;
    memoria->total_ms += pausa;
    if (pausa > memoria->max_ms) memoria->max_ms = pausa;
}
#endif

static long rss_kib(void)
{
#ifdef __linux__
    FILE *archivo = fopen("/proc/self/statm", "r");
    if (archivo) {
        long reservadas, residentes;
        int n = fscanf(archivo, "%ld %ld", &reservadas, &residentes);
        fclose(archivo);
        long pagina = sysconf(_SC_PAGESIZE);
        if (n == 2 && pagina > 0) return residentes * (pagina / 1024);
    }
#endif
    return 0;
}

static bool control_activo(int id, size_t *indice)
{
    size_t i;
    if (!lui_buscar_control(&ui, id, &i) || sesion.retirado[i]) return false;
    if (indice) *indice = i;
    return true;
}

static UIDespachoCallbackResultado host_despachar_evento(void *usuario, UIEvento evento)
{
    HostEventos *host = usuario;
    if (evento.tipo < UI_EVENTO_CLIC || evento.tipo > UI_EVENTO_CANCELAR)
        return UI_CB_DESP_CONTRATO;
    if (sesion.cerrar) return UI_CB_DESP_OMITIDO;
    size_t i;
    const char *nombre = "__ui_despachar";
    /* Biblioteca conserva Escape para su ID virtual 204. */
    if (lui_buscar_control(&ui, evento.id_widget, &i)) {
        if (sesion.retirado[i] ||
            (!ui.habilitados[i] && evento.tipo != UI_EVENTO_CANCELAR))
            return UI_CB_DESP_OMITIDO;
        const char *accion = sesion.acciones[i][evento.tipo - 1];
        if (*accion) nombre = accion;
    }
    UICBResultado r = ui_cb_despachar_evento(host->callbacks, nombre, evento);
    if (r == UI_CB_OK) {
        if (evento.tipo == UI_EVENTO_CLIC) host->ultimo_clic = evento.id_widget;
        return UI_CB_DESP_OK;
    }
    if (r == UI_CB_FUNCION_INEXISTENTE && !strcmp(nombre, "__ui_despachar"))
        return UI_CB_DESP_OMITIDO;
    if (r == UI_CB_ERROR_RECUPERADO) {
        fprintf(stderr, "Mictlán UI: falló el callback '%s' del control %d y la VM recuperó su estado.\n",
                nombre, evento.id_widget);
        return UI_CB_DESP_ERROR_RECUPERADO;
    }
    if (r == UI_CB_FUNCION_INEXISTENTE || r == UI_CB_FIRMA_INVALIDA ||
        r == UI_CB_ARGUMENTO_INVALIDO) {
        fprintf(stderr, "Mictlán UI: el control %d requiere una función '%s' sin argumentos.\n",
                evento.id_widget, nombre);
        return UI_CB_DESP_CONTRATO;
    }
    fprintf(stderr, "Mictlán UI: VM no reutilizable (%d).\n", (int)r);
    return UI_CB_DESP_VM_ERROR;
}

static void devolver_bool(lat_mv *mv, bool valor)
{
    latC_apilar(mv, valor ? latO_verdadero : latO_falso);
}

static void comprobar_configuracion(lat_mv *mv)
{
    if (sesion.configurada)
        latC_error(mv, "La estructura de la ventana se define al iniciar");
}

static void n_titulo(lat_mv *mv) {
    const char *texto = latC_checar_cadena(mv, latC_desapilar(mv));
    if (!lui_titulo(&ui, texto)) latC_error(mv, "%s", ui.error);
#ifndef MICTLAN_HOST_PRUEBAS
    if (sesion.configurada) SetWindowTitle(ui.titulo);
#endif
}
static void n_etiqueta(lat_mv *mv) {
    comprobar_configuracion(mv);
    const char *texto = latC_checar_cadena(mv, latC_desapilar(mv));
    if (!lui_agregar_control(&ui, siguiente_etiqueta++, UI_WIDGET_ETIQUETA, texto))
        latC_error(mv, "%s", ui.error);
}
static int leer_id(lat_mv *mv, lat_objeto *o) {
    if (o->tipo != T_NUMERIC) return -1;
    double n = latC_checar_numerico(mv, o);
    return isfinite(n) && n >= 0 && n < 10000 && floor(n) == n ? (int)n : -1;
}
static void crear_control(lat_mv *mv, UITipoWidget tipo) {
    comprobar_configuracion(mv);
    lat_objeto *o_texto=latC_desapilar(mv);
    lat_objeto *o_id=latC_desapilar(mv);
    const char *texto=latC_checar_cadena(mv,o_texto);
    if (!lui_agregar_control(&ui, leer_id(mv, o_id), tipo, texto))
        latC_error(mv, "%s", ui.error);
}
static void n_boton(lat_mv *mv) { crear_control(mv,UI_WIDGET_BOTON); }
static void n_campo(lat_mv *mv) { crear_control(mv,UI_WIDGET_CAMPO_TEXTO); }
static void n_etiqueta_id(lat_mv *mv) { crear_control(mv,UI_WIDGET_ETIQUETA); }
static void n_texto(lat_mv *mv) {
    int id = leer_id(mv, latC_desapilar(mv));
    const char *texto = control_activo(id, NULL) ? lui_texto(&ui, id) : NULL;
    if (texto) latC_apilar_string(mv,texto);
    else latC_apilar(mv,latO_falso);
}
static void n_poner_texto(lat_mv *mv) {
    lat_objeto *valor=latC_desapilar(mv);
    int id=leer_id(mv,latC_desapilar(mv));
    devolver_bool(mv, control_activo(id, NULL) && valor->tipo == T_STR &&
                       lui_establecer_texto(&ui, id, latC_checar_cadena(mv, valor)));
}
static void n_longitud_texto(lat_mv *mv) {
    int id = leer_id(mv, latC_desapilar(mv));
    const char *texto = control_activo(id, NULL) ? lui_texto(&ui, id) : NULL;
    size_t n=0;
    if (!ui_utf8_validar(texto,&n)) { latC_apilar(mv,latO_falso); return; }
    latC_apilar_double(mv,(double)n);
}
static void n_texto_valido(lat_mv *mv) {
    lat_objeto *valor = latC_desapilar(mv);
    int id = leer_id(mv, latC_desapilar(mv));
    devolver_bool(mv, control_activo(id, NULL) && valor->tipo == T_STR &&
                      lui_texto_valido(&ui, id, latC_checar_cadena(mv, valor)));
}
static void iniciar_contenedor(lat_mv *mv, UITipoNodo tipo)
{
    comprobar_configuracion(mv);
    double espacio = latC_checar_numerico(mv, latC_desapilar(mv));
    if (!isfinite(espacio) || espacio < 0)
        latC_error(mv, "La separación debe ser finita y no negativa");
    if (espacio > 3840)
        latC_error(mv, "La separación supera el tamaño máximo de ventana");
    if (!lui_iniciar_contenedor(&ui, tipo, (float)espacio))
        latC_error(mv, "%s", ui.error);
}

static void n_fila(lat_mv *mv) { iniciar_contenedor(mv, UI_NODO_FILA); }
static void n_columna(lat_mv *mv) { iniciar_contenedor(mv, UI_NODO_COLUMNA); }
static void n_fin(lat_mv *mv)
{
    comprobar_configuracion(mv);
    if (!lui_fin_contenedor(&ui)) latC_error(mv, "%s", ui.error);
}

static void n_ventana(lat_mv *mv)
{
    comprobar_configuracion(mv);
    double alto = latC_checar_numerico(mv, latC_desapilar(mv));
    double ancho = latC_checar_numerico(mv, latC_desapilar(mv));
    const char *titulo = latC_checar_cadena(mv, latC_desapilar(mv));
    if (!isfinite(ancho) || !isfinite(alto) || ancho < 600 || ancho > 3840 ||
        alto < 400 || alto > 2160 || trunc(ancho) != ancho || trunc(alto) != alto)
        latC_error(mv, "Dimensiones enteras fuera de rango (600–3840 × 400–2160)");
    if (!lui_titulo(&ui, titulo)) latC_error(mv, "%s", ui.error);
    sesion.ancho = (int)ancho;
    sesion.alto = (int)alto;
}

static void n_minimo(lat_mv *mv)
{
    comprobar_configuracion(mv);
    double alto = latC_checar_numerico(mv, latC_desapilar(mv));
    double ancho = latC_checar_numerico(mv, latC_desapilar(mv));
    if (!isfinite(ancho) || !isfinite(alto) || ancho < 600 || ancho > sesion.ancho ||
        alto < 400 || alto > sesion.alto || trunc(ancho) != ancho || trunc(alto) != alto)
        latC_error(mv, "El mínimo debe estar entre 600 × 400 y el tamaño inicial");
    sesion.minimo_ancho = (int)ancho;
    sesion.minimo_alto = (int)alto;
}

static void n_lienzo(lat_mv *mv)
{
    comprobar_configuracion(mv);
    int id = leer_id(mv, latC_desapilar(mv));
    if (sesion.lienzo_id >= 0) latC_error(mv, "La ventana admite un lienzo");
    if (!lui_agregar_control(&ui, id, UI_WIDGET_LIENZO, ""))
        latC_error(mv, "%s", ui.error);
    sesion.lienzo_id = id;
}

static void n_al_evento(lat_mv *mv)
{
    const char *nombre = latC_checar_cadena(mv, latC_desapilar(mv));
    double tipo = latC_checar_numerico(mv, latC_desapilar(mv));
    int id = leer_id(mv, latC_desapilar(mv));
    size_t i;
    if (!control_activo(id, &i) || !lui_habilitado(&ui, id) ||
        tipo < UI_EVENTO_CLIC || tipo > UI_EVENTO_CANCELAR || !isfinite(tipo) ||
        trunc(tipo) != tipo ||
        (ui.tipos[i] != UI_WIDGET_BOTON && ui.tipos[i] != UI_WIDGET_CAMPO_TEXTO) ||
        (tipo == UI_EVENTO_CLIC && ui.tipos[i] != UI_WIDGET_BOTON) ||
        (tipo == UI_EVENTO_SUBMIT && ui.tipos[i] != UI_WIDGET_CAMPO_TEXTO)) {
        latC_error(mv, "Asociación de evento inválida para el control %d", id);
        return;
    }
    if (strlen(nombre) >= MAX_ID_LENGTH)
        latC_error(mv, "El nombre del callback supera 63 bytes");
    lat_objeto *funcion = *nombre ? latO_obtener_contexto(mv, mv->contexto[0], nombre) : NULL;
    if (*nombre && (!funcion || funcion->tipo != T_FUN || funcion->nparams != 0 ||
                    funcion->es_vararg))
        latC_error(mv, "El callback '%s' debe ser una función global sin argumentos", nombre);
    memcpy(sesion.acciones[i][(int)tipo - 1], nombre, strlen(nombre) + 1);
}

static void n_enfocar(lat_mv *mv)
{
    int id = leer_id(mv, latC_desapilar(mv));
    devolver_bool(mv, control_activo(id, NULL) && lui_enfocar(&ui, id));
}

static void n_habilitar(lat_mv *mv)
{
    bool habilitado = latC_checar_logico(mv, latC_desapilar(mv));
    int id = leer_id(mv, latC_desapilar(mv));
    devolver_bool(mv, control_activo(id, NULL) && lui_habilitar(&ui, id, habilitado));
}

static void n_retirar(lat_mv *mv)
{
    int id = leer_id(mv, latC_desapilar(mv));
    size_t i;
    bool activo = control_activo(id, &i);
    if (activo) {
        sesion.retirado[i] = true;
        lui_habilitar(&ui, id, false);
        memset(sesion.acciones[i], 0, sizeof sesion.acciones[i]);
        ui.textos[i][0] = '\0';
    }
    devolver_bool(mv, activo);
}

static void n_cerrar(lat_mv *mv)
{
    (void)mv;
    sesion.cerrar = true;
}

static const lat_CReg libui[] = {
    {"titulo", n_titulo, 1},
    {"ventana", n_ventana, 3},
    {"minimo", n_minimo, 2},
    {"lienzo", n_lienzo, 1},
    {"al_evento", n_al_evento, 3},
    {"enfocar", n_enfocar, 1},
    {"habilitar", n_habilitar, 2},
    {"retirar", n_retirar, 1},
    {"cerrar", n_cerrar, 0},
    {"etiqueta", n_etiqueta, 1},
    {"boton", n_boton, 2},
    {"campo_texto", n_campo, 2},
    {"etiqueta_id", n_etiqueta_id, 2},
    {"texto", n_texto, 1},
    {"poner_texto", n_poner_texto, 2},
    {"texto_valido", n_texto_valido, 2},
    {"longitud_texto", n_longitud_texto, 1},
    {"iniciar_fila", n_fila, 1},
    {"iniciar_columna", n_columna, 1},
    {"fin_contenedor", n_fin, 0},
    {NULL, NULL, 0}
};

static void mostrar_uso(FILE *salida, const char *programa) {
    fprintf(salida, "Mictlán UI " MICTLAN_VERSION "\n"
                    "Uso: %s [--] archivo.mict  (también .lat)\n"
                    "     %s --ayuda\n"
                    "Sin archivo se carga scripts/app_ui.lat desde el directorio actual.\n",
            programa, programa);
#ifdef LAT_G_CADENAS_EXPLICITAS
    fputs("Usa --gc-experimental antes de -- para probar la recolección entre callbacks.\n", salida);
#endif
}

#if defined(__linux__) && !defined(MICTLAN_HOST_PRUEBAS)
static void cargar_icono(void)
{
    /* Al extraer el paquete, el icono viaja junto al prefijo del ejecutable. */
    char ruta[4096];
    ssize_t n = readlink("/proc/self/exe", ruta, sizeof ruta - 1);
    if (n <= 0 || (size_t)n == sizeof ruta - 1) return;
    ruta[n] = '\0';
    char *barra = strrchr(ruta, '/');
    const char icono[] = "/../share/mictlan/recursos/Mictlan.png";
    if (!barra || (size_t)(barra - ruta) + sizeof icono > sizeof ruta) return;
    memcpy(barra, icono, sizeof icono);
    if (!FileExists(ruta)) return;
    Image imagen = LoadImage(ruta);
    if (imagen.data) {
        SetWindowIcon(imagen);
        UnloadImage(imagen);
    }
}
#endif

int main(int argc, char **argv) {
    const char *ruta = "scripts/app_ui.lat";
    bool gc_solicitado = argc > 1 && !strcmp(argv[1], "--gc-experimental");
    if (argc == 2 && (!strcmp(argv[1], "--ayuda") || !strcmp(argv[1], "--help"))) {
        mostrar_uso(stdout, argv[0]);
        return EXIT_SUCCESS;
    }
    if (argc == 2 && !strcmp(argv[1], "--version")) {
        puts("Mictlán UI " MICTLAN_VERSION);
        return EXIT_SUCCESS;
    }
    if (gc_solicitado) {
        --argc;
        ++argv;
    }
    if (argc == 3 && !strcmp(argv[1], "--") && argv[2][0]) {
        ruta = argv[2];
    } else if (argc == 2 && argv[1][0] && argv[1][0] != '-') {
        ruta = argv[1];
    } else if (argc != 1) {
        mostrar_uso(stderr, argv[0]);
        return EXIT_FAILURE;
    }

    lat_mv *mv = NULL;
    ast *nodo = NULL;
    lat_objeto *funcion = NULL;
    UIBiblioteca *biblioteca = NULL;
    UICBContexto callbacks = {0};
    UIDespachador despachador = {0};
    bool ventana_abierta = false;
    bool vm_comprometida = false;
    HostMemoria memoria = {.estado = -1};
    int salida = EXIT_FAILURE;
    HostEventos eventos = {&callbacks, -1};
    memset(&sesion, 0, sizeof sesion);
    sesion.ancho = 900;
    sesion.alto = 600;
    sesion.minimo_ancho = 600;
    sesion.minimo_alto = 400;
    sesion.lienzo_id = -1;
    siguiente_etiqueta = 10000;
    mictlan_lienzo_inicializar(&lienzo_graficos);
    plano_graficos.cantidad = 0;
    if (!lui_inicializar(&ui)) goto cerrar;

    UIEvento memoria_eventos[64] = {0};
    UIColaEventos cola_eventos = {0};

    if (ui_eventos_inicializar(
            &cola_eventos, memoria_eventos, 64)
            != UI_EVENTOS_OK) {
        fprintf(stderr, "Error al iniciar la cola\n");
        goto cerrar;
    }
    mv = latC_crear_mv();
    if (!mv) { fprintf(stderr, "No se pudo crear VM\n"); goto cerrar; }
    latC_abrir_liblatino(mv, "ui", libui);
    mictlan_ciencia_ffi_registrar(mv);
    mictlan_graficos_ffi_registrar(
        mv,
        &lienzo_graficos
    );
    mictlan_graficos_ffi_conectar_plano(&plano_graficos);
    biblioteca = ui_biblioteca_crear(mv, NULL);
    if (!biblioteca) { fprintf(stderr, "LatinoUI: no se pudo crear biblioteca\n"); goto cerrar; }
    ui_biblioteca_conectar_ui(biblioteca, &ui);
    if (ui_cb_inicializar(&callbacks, mv) != UI_CB_OK ||
        ui_cb_registrar(&callbacks) != UI_CB_OK) {
        fprintf(stderr, "LatinoUI: no se pudo registrar ui_cb\n");
        goto cerrar;
    }
    if (ui_despachador_inicializar_eventos(&despachador, &cola_eventos,
                                  host_despachar_evento, &eventos) != UI_DESP_OK) {
        fprintf(stderr, "LatinoUI: no se pudo iniciar despachador\n");
        goto cerrar;
    }
    if (gc_solicitado) {
#ifdef LAT_G_CADENAS_EXPLICITAS
        if (!habilitar_memoria(&memoria, mv)) {
            fprintf(stderr, "Mictlán UI: no se pudo preparar la recolección experimental.\n");
            goto cerrar;
        }
        for (const lat_CReg *f = libui; f->nombre; ++f) {
            if (latG_autorizar(mv, f->cfun) != LAT_G_OK) goto cerrar;
        }
#else
        fprintf(stderr, "Mictlán UI: este Core carece del recolector de cadenas de P1.1.\n");
        goto cerrar;
#endif
    }

    mv->nombre_archivo = (char *)ruta;
    mv->global->REPL = false;
    int estado = 0;
    nodo = latA_analizar_arch((char *)ruta, &estado);
    if (estado || !nodo) {
        fprintf(stderr, "No se pudo analizar %s\n", ruta);
        goto cerrar;
    }
    funcion = latC_analizar(mv, nodo);
    if (!funcion) {
        fprintf(stderr, "No se pudo preparar script\n");
        goto cerrar;
    }
    const int previo = mv->ptrprevio;
    const int argumentos = mv->prev_args;
    int resultado = latC_llamar_funcion(mv, funcion);
    vm_comprometida = !ui_cb_vm_en_reposo(mv) ||
        (resultado && (resultado != LAT_ERRRUN || mv->ptrprevio != previo ||
                       mv->prev_args != argumentos));
    if (resultado || vm_comprometida) {
        fprintf(stderr, "Mictlán UI: falló el programa inicial.\n");
        goto cerrar;
    }
    latO_destruir(mv, funcion);
    funcion = NULL;
#ifdef LAT_G_CADENAS_EXPLICITAS
    recolectar_memoria(&memoria, &callbacks, 0);
#endif
    if (!lui_validar(&ui)) {
        fprintf(stderr, "LatinoUI: estructura invalida: %s\n", ui.error);
        goto cerrar;
    }
    if (sesion.ancho < sesion.minimo_ancho || sesion.alto < sesion.minimo_alto) {
        fprintf(stderr, "Mictlán UI: el tamaño inicial es menor que el mínimo.\n");
        goto cerrar;
    }

    sesion.configurada = true;
    if (sesion.cerrar) { salida = EXIT_SUCCESS; goto cerrar; }

    /* El AST se conserva hasta cerrar. Core conserva el bytecode incluso
       después de liberar el descriptor inicial. */

    SetConfigFlags(FLAG_WINDOW_RESIZABLE);
    InitWindow(sesion.ancho, sesion.alto, ui.titulo);
    ventana_abierta = IsWindowReady();
    if (!ventana_abierta) {
        fprintf(stderr, "LatinoUI: no se pudo abrir la ventana\n");
        goto cerrar;
    }
#if defined(__linux__) && !defined(MICTLAN_HOST_PRUEBAS)
    cargar_icono();
#endif
    SetExitKey(KEY_NULL);
    SetWindowMinSize(sesion.minimo_ancho, sesion.minimo_alto);
    UIEvento inicial;
    if (ui.foco == UI_NODO_NULO) (void)lui_tecla(&ui, UI_TECLA_TAB, &inicial);
    SetTargetFPS(60);
    int ancho_anterior = -1, alto_anterior = -1;
    bool valido = false;
    double inicio = 0.0;
    (void)ui_despachador_reloj_monotonico(NULL, &inicio);
    size_t cuadros = 0;
    size_t memoria_pico = mv->memoria_usada;
    for (;;) {
        if (WindowShouldClose()) {
            if (!ui_biblioteca_protege_cierre(biblioteca) || despachador.estado_vm != UI_VM_SANA) break;
            ui_biblioteca_pedir_cierre(biblioteca);
        }
        if (ui_biblioteca_consumir_cierre(biblioteca)) break;
        ui_biblioteca_sincronizar_ui(biblioteca);
        int ancho = GetScreenWidth(), alto = GetScreenHeight();
        if (ancho != ancho_anterior || alto != alto_anterior) {
            UIRect area = {24.0f, 70.0f, (float)ancho - 48.0f, (float)alto - 110.0f};
            valido = lui_calcular(&ui, area);
            ancho_anterior = ancho;
            alto_anterior = alto;
        }
#ifdef MICTLAN_HOST_PRUEBAS
        bool enfocada = true;
#else
        bool enfocada = IsWindowFocused();
#endif
        if (valido && enfocada && IsMouseButtonPressed(MOUSE_BUTTON_LEFT)) {
            Vector2 p = GetMousePosition();
            for (size_t i = 0; i < ui.arbol.cantidad; ++i) {
                if (ui.nodos[i].tipo != UI_NODO_WIDGET || sesion.retirado[i] ||
                    (ui.tipos[i] != UI_WIDGET_BOTON && ui.tipos[i] != UI_WIDGET_CAMPO_TEXTO) ||
                    !ui.habilitados[i]) continue;
                UIRect b = ui.rectangulos[i];
                Rectangle r = {b.x, b.y, b.ancho, b.alto};
                if (CheckCollisionPointRec(p, r)) {
                   (void)lui_enfocar(&ui,ui.nodos[i].id_widget);
                   if (ui.tipos[i] == UI_WIDGET_CAMPO_TEXTO) break;
                   UIEvento nuevo = {
                       UI_EVENTO_CLIC,
                       ui.nodos[i].id_widget
                   };

                   UIDespachoResultado estado_cola =
                       ui_despachador_encolar(&despachador, nuevo);

                   if (estado_cola != UI_DESP_OK) {
                       fprintf(stderr,
                           "No se pudo encolar evento %d (codigo %d)\n",
                           nuevo.id_widget, (int)estado_cola);
                   }
                    break;
                }
            }
        }

       if (valido && enfocada && despachador.estado_vm == UI_VM_SANA) {
           /* Un solo gesto de control por frame. La escritura queda en C;
              consultar ui.texto() es lo que crea una cadena en la VM. */
           UIEvento evento;
           bool emitir=false;
           if (IsKeyPressed(KEY_TAB))
               emitir=lui_tecla(&ui,(IsKeyDown(KEY_LEFT_SHIFT) || IsKeyDown(KEY_RIGHT_SHIFT))
                   ? UI_TECLA_RETROTAB : UI_TECLA_TAB,&evento);
           else if (IsKeyPressed(KEY_ESCAPE)) {
               if (ui_biblioteca_protege_cierre(biblioteca)) {
                   evento=(UIEvento){UI_EVENTO_CANCELAR,204}; emitir=true;
               } else emitir=lui_tecla(&ui,UI_TECLA_ESCAPE,&evento);
           }
           else {
               for (int punto=GetCharPressed();punto>0;punto=GetCharPressed())
                   (void)lui_caracter(&ui,(unsigned int)punto);
               bool borrar = IsKeyPressed(KEY_BACKSPACE);
#ifndef MICTLAN_HOST_PRUEBAS
               borrar = borrar || IsKeyPressedRepeat(KEY_BACKSPACE);
#endif
               if (borrar) (void)lui_tecla(&ui, UI_TECLA_BORRAR, &evento);
               if (IsKeyPressed(KEY_ENTER)) emitir=lui_tecla(&ui,UI_TECLA_ENTER,&evento);
           }
           if (emitir && ui_despachador_encolar(&despachador,evento)!=UI_DESP_OK)
               fprintf(stderr,"LatinoUI: cola llena; evento de teclado rechazado\n");
       }

       ui_biblioteca_sincronizar_ui(biblioteca);
       UIDespachoResultado estado_frame =
           ui_despachador_procesar_frame(&despachador);
        if (mv->memoria_usada > memoria_pico) memoria_pico = mv->memoria_usada;
        if (estado_frame == UI_DESP_ERR_VM_COMPROMETIDA || estado_frame == UI_DESP_ERR_CALLBACK)
            goto terminar_ventana;
        if (estado_frame == UI_DESP_ERR_CONTRATO) {
            fprintf(stderr, "Mictlán UI: evento rechazado por contrato.\n");
            goto terminar_ventana;
        }
        if (estado_frame == UI_DESP_ERR_RELOJ) {
            fprintf(stderr, "Mictlán UI: reloj del despachador no disponible.\n");
            goto terminar_ventana;
        }
#ifdef LAT_G_CADENAS_EXPLICITAS
        if (memoria.activo &&
            (despachador.metricas.eventos_despachados - memoria.ultimo_evento >= GC_EVENTOS ||
             (mv->memoria_usada > memoria.bytes_base &&
              mv->memoria_usada - memoria.bytes_base >= GC_CRECIMIENTO_BYTES)))
            recolectar_memoria(&memoria, &callbacks, despachador.metricas.eventos_despachados);
#endif
        if (sesion.cerrar || ui_biblioteca_consumir_cierre(biblioteca)) break;
       BeginDrawing();
        ClearBackground(RAYWHITE);
        DrawText(ui.titulo, 24, 19, 28, DARKBLUE);
        if (!valido) {
            DrawText("Espacio insuficiente para layout", 24, 85, 24, MAROON);
        } else {
            for (size_t i = 0; i < ui.arbol.cantidad; i++) {
                UIRect b = ui.rectangulos[i];
                Rectangle r = {b.x, b.y, b.ancho, b.alto};
                if (sesion.retirado[i]) continue;
                if (ui.nodos[i].tipo == UI_NODO_WIDGET) {
                    if (ui.tipos[i] == UI_WIDGET_LIENZO) {
                        DrawRectangleRec(r, (Color){250, 253, 255, 255});
                        DrawRectangleLinesEx(r, 1.0f, LIGHTGRAY);
#ifndef MICTLAN_HOST_PRUEBAS
                        mictlan_renderizar_lineas(&plano_graficos, b);
#endif
                        continue;
                    }
                    bool boton = ui.tipos[i] == UI_WIDGET_BOTON;
                    DrawRectangleRec(r, boton && ui.habilitados[i] ? SKYBLUE : (Color){231, 239, 247, 255});
                    DrawRectangleLinesEx(r, ui.foco==i ? 3.0f : 1.0f,
                                         ui.foco==i ? DARKBLUE : GRAY);
                    BeginScissorMode((int)r.x, (int)r.y, (int)r.width, (int)r.height);
                    int fuente = (int)fminf(24.0f, fmaxf(10.0f, b.alto - 12.0f));
                    const char *texto = ui.textos[i];
#ifndef MICTLAN_HOST_PRUEBAS
                    if (ui.foco == i && ui.tipos[i] == UI_WIDGET_CAMPO_TEXTO) {
                        while (*texto && MeasureText(texto, fuente) > r.width - 18) {
                            ++texto;
                            while (((unsigned char)*texto & 0xc0) == 0x80) ++texto;
                        }
                    }
#endif
                    DrawText(texto, (int)b.x + 9, (int)b.y + 6,
                             fuente, ui.habilitados[i] ? DARKBLUE : GRAY);
                    EndScissorMode();
                } else {
                    DrawRectangleLinesEx(r, 1.0f, LIGHTGRAY);
                }
            }
        }
        DrawText(TextFormat("Ultimo clic: %d", eventos.ultimo_clic), 24, GetScreenHeight() - 31, 20, DARKGRAY);

        #ifndef MICTLAN_HOST_PRUEBAS
            mictlan_renderizar_lienzo(&lienzo_graficos);
        #endif
        
        EndDrawing();
        ++cuadros;
    }
    salida = EXIT_SUCCESS;
terminar_ventana:
#ifdef LAT_G_CADENAS_EXPLICITAS
    if (memoria.activo && despachador.metricas.eventos_despachados != memoria.ultimo_evento)
        recolectar_memoria(&memoria, &callbacks, despachador.metricas.eventos_despachados);
#endif
    if (getenv("MICTLAN_UI_METRICAS")) {
        double fin = inicio;
        (void)ui_despachador_reloj_monotonico(NULL, &fin);
        size_t pico = memoria_pico;
        long rss_pico = 0;
#ifdef LAT_G_CADENAS_EXPLICITAS
        latG_medicion datos = {0};
        if (latG_medir(mv, &datos) == LAT_G_OK) pico = datos.pico_bytes_vm;
#endif
#ifdef __linux__
        struct rusage uso;
        if (getrusage(RUSAGE_SELF, &uso) == 0) rss_pico = uso.ru_maxrss;
#endif
        fprintf(stdout, "MICTLAN_UI_METRICAS {\"cuadros\":%zu,\"eventos\":%zu,"
                "\"eventos_entregados\":%zu,\"callback_max_ms\":%.6f,"
                "\"ms\":%.6f,\"bytes_vm\":%zu,\"bytes_vm_pico_muestreado\":%zu,"
                "\"cadenas\":%u,\"ancho\":%d,\"alto\":%d,\"lineas\":%zu,"
                "\"bytes_vm_pico\":%zu,\"rss_kib\":%ld,\"rss_pico_kib\":%ld,"
                "\"gc_estado\":%d,\"gc_recolecciones\":%zu,\"gc_reservas\":%zu,\"gc_bytes\":%zu,"
                "\"gc_total_ms\":%.6f,\"gc_max_ms\":%.6f}\n",
                cuadros, despachador.metricas.eventos_consumidos,
                despachador.metricas.eventos_despachados,
                despachador.metricas.max_callback_ms, fin - inicio,
                mv->memoria_usada, memoria_pico, mv->global->strt.nuse,
                ancho_anterior, alto_anterior, plano_graficos.cantidad,
                pico, rss_kib(), rss_pico, memoria.estado, memoria.recolecciones,
                memoria.reservas, memoria.bytes, memoria.total_ms, memoria.max_ms);
    }

cerrar:
    if (ventana_abierta) CloseWindow();
    ui_cb_desregistrar(&callbacks);
    mictlan_graficos_ffi_desconectar();
    ui_biblioteca_destruir(biblioteca);
    if (vm_comprometida || despachador.estado_vm == UI_VM_COMPROMETIDA ||
        callbacks.inutilizada) {
        /* Los recursos externos ya se cerraron. Una VM incoherente queda
           aislada hasta que termina el proceso. */
        fprintf(stderr, "LatinoUI: cierre con VM comprometida; se omite destructor\n");
        return EXIT_FAILURE;
    }
    if (mv) {
        if (funcion) latO_destruir(mv, funcion);
        latC_destruir_mv(mv);
    }
    if (nodo) latA_destruir(nodo);
    return salida;
}

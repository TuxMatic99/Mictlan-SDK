/* Regresion contra liblatino.so real. No incluye ni sustituye codigo de Core. */
#include "latino.h"
#include "latast.h"
#include "latobj.h"
#include "mictlan_ciencia_ffi.h"
#include <errno.h>
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

_Static_assert(LAT_ERRRUN == 2, "El contrato interno requiere LAT_ERRRUN == 2");

typedef struct {
    ast *tree;
    lat_objeto *function;
} Program;

typedef struct {
    lat_objeto *stack, *context;
    lat_global *global;
    struct lat_longjmp *error;
    int ptrctx, ptrpila, numejec, enBucle;
    bool enClase;
} Baseline;

static unsigned failures, calls;

static Program compile_program(lat_mv *mv, const char *source)
{
    int state = -1;
    Program program = {NULL, NULL};
    /* El parser recibe char *, aunque no modifica el texto de entrada. */
    program.tree = latA_analizar_exp((char *)source, &state);
    if (program.tree != NULL && state == 0)
        program.function = latC_analizar(mv, program.tree);
    return program;
}

static int stack_coherent(const lat_mv *mv)
{
    /* Comparar direcciones como enteros evita restar punteros invalidos. */
    return mv->ptrpila >= 0 && mv->ptrpila < MAX_STACK_SIZE &&
        (uintptr_t)mv->tope == (uintptr_t)mv->pila +
            (size_t)mv->ptrpila * sizeof(lat_objeto);
}

static int check_call(lat_mv *mv, lat_objeto *function, const Baseline *base,
                      const char *name, unsigned cycle, int expected, int returns_number)
{
    int before_ctx = mv->ptrctx, before_num = mv->numejec, before_stack = mv->ptrpila;
    int state = latC_llamar_funcion(mv, function);
    int raw_stack = mv->ptrpila;
    int result_ok = 1;
    if (returns_number) {
        result_ok = state == 0 && stack_coherent(mv) &&
            mv->ptrpila == base->ptrpila + 1;
        if (result_ok) {
            /* Consumir solo el retorno documentado; nunca reparar la pila. */
            lat_objeto *value = latC_desapilar(mv);
            result_ok = value->tipo == T_NUMERIC && fabs(getNumerico(value) - 5.0) < 1e-12;
        }
    }
    int context_ok = mv->ptrctx == base->ptrctx &&
        mv->contexto_actual == base->context && mv->contexto[0] == base->context;
    int stack_ok = stack_coherent(mv) && mv->pila == base->stack &&
        mv->ptrpila == base->ptrpila;
    int control_ok = mv->error == base->error && mv->global == base->global &&
        mv->enBucle == base->enBucle && mv->enClase == base->enClase &&
        mv->var_cache_next >= 0 && mv->var_cache_next < VAR_CACHE_SIZE &&
        mv->ptrprevio >= 0 && mv->ptrprevio < MAX_STACK_SIZE &&
        mv->prev_args >= 0 && mv->prev_args < MAX_STACK_SIZE;
    int ok = state == expected && result_ok && context_ok && stack_ok && control_ok &&
        mv->numejec == base->numejec;
    ++calls;
    if (!ok) ++failures;
    printf("{\"event\":\"call\",\"cycle\":%u,\"case\":\"%s\","
           "\"state\":%d,\"expected_state\":%d,"
           "\"before\":{\"ptrctx\":%d,\"ptrpila\":%d,\"numejec\":%d},"
           "\"after\":{\"ptrctx\":%d,\"ptrpila_raw\":%d,\"ptrpila\":%d,"
           "\"numejec\":%d,\"ptrprevio\":%d,\"prev_args\":%d},"
           "\"context_ok\":%s,\"stack_ok\":%s,\"control_ok\":%s,"
           "\"result_ok\":%s,\"ok\":%s}\n",
           cycle, name, state, expected, before_ctx, before_stack, before_num,
           mv->ptrctx, raw_stack, mv->ptrpila, mv->numejec, mv->ptrprevio, mv->prev_args,
           context_ok ? "true" : "false", stack_ok ? "true" : "false",
           control_ok ? "true" : "false", result_ok ? "true" : "false", ok ? "true" : "false");
    return ok;
}

static int safe_to_continue(const lat_mv *mv, const Baseline *base)
{
    /* Core publicado tiene 256 contextos y limite recursivo 1024.
       Reservar margen para la siguiente llamada. Alcanzarlo es FALLO, no skip. */
    return stack_coherent(mv) && mv->pila == base->stack && mv->ptrpila == base->ptrpila &&
        mv->error == base->error && mv->ptrctx >= 0 && mv->ptrctx < 32 &&
        mv->numejec >= 0 && mv->numejec < 128;
}

int main(int argc, char **argv)
{
    if (argc != 3 || (strcmp(argv[1], "control") && strcmp(argv[1], "directa") &&
                      strcmp(argv[1], "anidada") && strcmp(argv[1], "pila"))) {
        fprintf(stderr, "Uso: %s control|directa|anidada|pila ciclos(1..1000)\n", argv[0]);
        return 3;
    }
    char *end;
    errno = 0;
    long requested = strtol(argv[2], &end, 10);
    if (errno || !*argv[2] || *end || requested < 1 || requested > 1000) return 3;
    setvbuf(stdout, NULL, _IOLBF, 0);
    lat_mv *mv = latC_crear_mv();
    if (!mv) return 1;
    mv->nombre_archivo = "p03_recuperacion_vm";
    mv->global->REPL = false;
    mictlan_ciencia_ffi_registrar(mv);
    Baseline base = {mv->pila, mv->contexto[0], mv->global, mv->error,
                     mv->ptrctx, mv->ptrpila, mv->numejec, mv->enBucle, mv->enClase};
    Program programs[3] = {{0}};
    programs[0] = compile_program(mv,
        "funcion p03_valida_interna()\n retorno ciencia.longitud2(3, 4)\nfin\n"
        "funcion p03_valida()\n retorno p03_valida_interna()\nfin\n"
        "funcion p03_tipo_interna()\n retorno ciencia.sumar2(\"texto\", 4, 5, 12)\nfin\n"
        "funcion p03_tipo()\n retorno p03_tipo_interna()\nfin\n"
        "funcion p03_rango_interna()\n retorno ciencia.sumar2(1e308, 0, 1e308, 0)\nfin\n"
        "funcion p03_rango()\n retorno p03_rango_interna()\nfin\n");
    const int nested = !strcmp(argv[1], "anidada");
    programs[1] = compile_program(mv, !strcmp(argv[1], "pila") ?
        "resultado = ciencia.sumar2(3, 4, 5, \"texto\")\n" : nested ? "p03_tipo()\n" :
        "resultado = ciencia.sumar2(\"texto\", 4, 5, 12)\n");
    programs[2] = compile_program(mv, nested ? "p03_rango()\n" :
        "resultado = ciencia.sumar2(1e308, 0, 1e308, 0)\n");
    unsigned completed = 0;
    int guarded = 0;
    if (!programs[0].function || !programs[1].function || !programs[2].function ||
        base.ptrctx != 0 || base.ptrpila != 0 || base.numejec != 0) {
        ++failures;
        goto cleanup;
    }
    if (!check_call(mv, programs[0].function, &base, "definiciones", 0, 0, 0)) goto cleanup;
    lat_objeto *valid = latO_obtener_contexto(mv, base.context, "p03_valida");
    if (!valid || valid->tipo != T_FUN) { ++failures; goto cleanup; }
    for (unsigned cycle = 1; cycle <= (unsigned)requested; ++cycle) {
        /* Alternar error/valida y repetir errores consecutivos en la misma VM. */
        const unsigned sequence[] = {1, 0, 2, 0, 1, 1, 0, 2, 2, 0};
        unsigned count = !strcmp(argv[1], "control") ? 1 : sizeof(sequence) / sizeof(sequence[0]);
        for (unsigned j = 0; j < count; ++j) {
            unsigned which = count == 1 ? 0 : sequence[j];
            if (!safe_to_continue(mv, &base)) { guarded = 1; ++failures; goto cleanup; }
            check_call(mv, which ? programs[which].function : valid, &base,
                       which == 1 ? "error_tipo" : which == 2 ? "error_rango" : "valida_anidada",
                       cycle, which ? LAT_ERRRUN : 0, !which);
        }
        ++completed;
    }
cleanup:
    /* Destructores reales, tambien despues de errores. Sin limpiar contadores. */
    for (unsigned i = 0; i < 3; ++i) {
        if (programs[i].function) latO_destruir(mv, programs[i].function);
        if (programs[i].tree) latA_destruir(programs[i].tree);
    }
    latC_destruir_mv(mv);
    printf("{\"event\":\"summary\",\"mode\":\"%s\",\"requested_cycles\":%ld,"
           "\"completed_cycles\":%u,\"calls\":%u,\"failed_calls_or_guards\":%u,"
           "\"safety_stop\":%s,\"status\":\"%s\"}\n", argv[1], requested, completed,
           calls, failures, guarded ? "true" : "false",
           failures || completed != (unsigned)requested ? "FAIL" : "PASS_FUNCTIONAL");
    return failures || completed != (unsigned)requested ? 1 : 0;
}

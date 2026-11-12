/* Contratos reales: identidad, valores, referencias y destructor, sin mocks.
 * CHECK permanece activo en Release. No se cambia la propiedad en Core/SDK. */
#include "latino.h"
#include "latast.h"
#include "latobj.h"
#include "latlist.h"
#include "latrecurso.h"
#include "latlista_recursos.h"
#include "mictlan_ciencia_ffi.h"
#include <stdio.h>
#include <string.h>

#define CHECK(x) do { if (!(x)) { \
    fprintf(stderr, "P033_ASSERT linea %d: %s\n", __LINE__, #x); return 1; \
} } while (0)

static unsigned destrucciones;
static void destruir(lat_mv *mv, void *dato)
{
    ++destrucciones;
    latO_destruir(mv, dato);
}

static int recursos(const char *caso)
{
    lat_mv mv = {0};
    for (unsigned i = 0; i < 200; ++i) {
        unsigned antes = destrucciones;
        lat_objeto *dato = latC_crear_numerico(&mv, 8);
        lat_recurso *r = latR_crear(&mv, dato, destruir);
        lat_lista_recursos *a = latLR_crear(&mv), *b = latLR_crear(&mv);
        CHECK(r && a && b && latR_dato(r) == dato);
        CHECK(latLR_agregar(&mv, a, r) && latLR_agregar(&mv, b, r));
        CHECK(latR_propietarios(r) == 3);
        CHECK(latLR_obtener(a, 0) == dato && latLR_obtener(b, 0) == dato);
        CHECK(!latLR_eliminar(&mv, a, -1) && !latLR_reemplazar(&mv, a, 1, r));
        CHECK(latLR_obtener(a, -1) == NULL && latLR_obtener(a, 1) == NULL);
        CHECK(latLR_longitud(a) == 1 && latR_propietarios(r) == 3);
        if (!strcmp(caso, "repetidos")) {
            CHECK(latLR_agregar(&mv, a, r));
            CHECK(latR_propietarios(r) == 4 && latLR_obtener(a, 1) == dato);
            CHECK(latLR_eliminar(&mv, a, 0));
            CHECK(latR_propietarios(r) == 3 && destrucciones == antes);
            CHECK(latLR_obtener(a, 0) == dato);
        }
        if (!strcmp(caso, "reemplazo")) {
            CHECK(latLR_reemplazar(&mv, a, 0, r));
            CHECK(latR_propietarios(r) == 3 && destrucciones == antes);
            lat_objeto *otro = latC_crear_numerico(&mv, 17);
            lat_recurso *s = latR_crear(&mv, otro, destruir);
            CHECK(latLR_reemplazar(&mv, a, 0, s));
            CHECK(latR_propietarios(r) == 2 && latR_propietarios(s) == 2);
            CHECK(latLR_obtener(a, 0) == otro && latLR_obtener(b, 0) == dato);
            latR_soltar(&mv, &s);
            CHECK(s == NULL && destrucciones == antes);
        }
        latR_soltar(&mv, &r);
        CHECK(r == NULL);
        latLR_destruir(&mv, &a);
        unsigned extra = !strcmp(caso, "reemplazo") ? 1 : 0;
        CHECK(a == NULL && destrucciones == antes + extra);
        CHECK(latLR_obtener(b, 0) == dato && getNumerico(dato) == 8);
        latLR_destruir(&mv, &b);
        CHECK(b == NULL && destrucciones == antes + extra + 1);
        CHECK(mv.memoria_usada == 0);
    }
    printf("{\"case\":\"%s\",\"cycles\":200,\"destructions\":%u,\"ok\":true}\n", caso, destrucciones);
    return 0;
}

static int ejecutar(lat_mv *mv, const char *texto)
{
    int estado = -1;
    ast *arbol = latA_analizar_exp((char *)texto, &estado);
    CHECK(arbol && estado == 0);
    lat_objeto *funcion = latC_analizar(mv, arbol);
    CHECK(funcion);
    estado = latC_llamar_funcion(mv, funcion);
    latO_destruir(mv, funcion);
    latA_destruir(arbol);
    CHECK(estado == 0);
    CHECK(mv->ptrpila == 0 && mv->tope == mv->pila && mv->ptrctx == 0 && mv->numejec == 0);
    return 0;
}

static int alias_ffi(void)
{
    lat_mv *mv = latC_crear_mv();
    CHECK(mv);
    mv->nombre_archivo = "p033_alias_ffi";
    mv->global->REPL = false;
    mictlan_ciencia_ffi_registrar(mv);
    CHECK(ejecutar(mv, "original = ciencia.sumar2(3, 4, 5, 12)\nalias = original\n") == 0);
    lat_objeto *a = latO_obtener_contexto(mv, mv->contexto[0], "original");
    lat_objeto *b = latO_obtener_contexto(mv, mv->contexto[0], "alias");
    CHECK(a && b && a->tipo == T_LIST && b->tipo == T_LIST);
    lista *identidad = getLista(a);
    CHECK(identidad == getLista(b) && latL_longitud(identidad) == 2);
    CHECK(getNumerico(latL_obtener_elemento(mv, identidad, 0)) == 8);
    CHECK(getNumerico(latL_obtener_elemento(mv, identidad, 1)) == 16);
    CHECK(ejecutar(mv, "alias[0] = 99\noriginal = [7, 14]\nalias[1] = 77\n") == 0);
    a = latO_obtener_contexto(mv, mv->contexto[0], "original");
    b = latO_obtener_contexto(mv, mv->contexto[0], "alias");
    CHECK(a && b && a->tipo == T_LIST && b->tipo == T_LIST);
    CHECK(getLista(b) == identidad && getLista(a) != identidad);
    CHECK(getNumerico(latL_obtener_elemento(mv, getLista(a), 0)) == 7);
    CHECK(getNumerico(latL_obtener_elemento(mv, identidad, 0)) == 99);
    CHECK(getNumerico(latL_obtener_elemento(mv, identidad, 1)) == 77);
    /* Uso normal del host: cerrar la VM. No destruir manualmente los payloads
       prestados para tapar las fugas que siguen pendientes en este camino. */
    latC_destruir_mv(mv);
    puts("{\"case\":\"alias_ffi\",\"identity\":true,\"values\":true,\"ok\":true}");
    return 0;
}

int main(int argc, char **argv)
{
    setvbuf(stdout, NULL, _IOLBF, 0);
    if (argc != 2) return 3;
    if (!strcmp(argv[1], "alias_ffi")) return alias_ffi();
    if (!strcmp(argv[1], "identidad") || !strcmp(argv[1], "repetidos") ||
        !strcmp(argv[1], "reemplazo")) return recursos(argv[1]);
    return 3;
}

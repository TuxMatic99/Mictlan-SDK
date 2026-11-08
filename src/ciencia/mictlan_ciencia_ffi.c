
#include "mictlan_ciencia_ffi.h"
#include "mictlan_vectores2d.h"

#include "latobj.h"

#include <math.h>
#include <stddef.h>

/*
 * Funcion visible desde Mictlan:
 *
 * ciencia.longitud2(x, y)
 */
static void n_ciencia_longitud2(lat_mv *mv)
{
    /* Los argumentos salen en orden inverso. */
    double y = latC_checar_numerico(
        mv, latC_desapilar(mv)
    );

    double x = latC_checar_numerico(
        mv, latC_desapilar(mv)
    );

    /* Rechazar valores no finitos. */
    if (!isfinite(x) || !isfinite(y)) {
        latC_error(mv,
            "ciencia.longitud2: coordenadas no finitas");
        return;
    }

    /* Utilizar nuestra biblioteca matematica. */
    MictlanVector2 vector =
        mictlan_vector2_crear(x, y);

    double longitud =
        mictlan_vector2_longitud(vector);

    if (!isfinite(longitud)) {
        latC_error(mv,
            "ciencia.longitud2: resultado fuera de rango");
        return;
    }

    /* Devolver el resultado al programa Mictlan. */
    latC_apilar_double(mv, longitud);
}


/*
 * Producto punto de dos vectores bidimensionales.
 *
 * Desde Mictlan:
 * ciencia.producto_punto2(ax, ay, bx, by)
 */
static void n_ciencia_producto_punto2(lat_mv *mv)
{
    /* Los argumentos se extraen en orden inverso. */
    double by = latC_checar_numerico(
        mv, latC_desapilar(mv)
    );

    double bx = latC_checar_numerico(
        mv, latC_desapilar(mv)
    );

    double ay = latC_checar_numerico(
        mv, latC_desapilar(mv)
    );

    double ax = latC_checar_numerico(
        mv, latC_desapilar(mv)
    );

    /* Validar las cuatro coordenadas. */
    if (!isfinite(ax) || !isfinite(ay) ||
        !isfinite(bx) || !isfinite(by)) {

        latC_error(mv,
            "ciencia.producto_punto2: "
            "coordenadas no finitas");
        return;
    }

    MictlanVector2 a = mictlan_vector2_crear(ax, ay);
    MictlanVector2 b = mictlan_vector2_crear(bx, by);

    double resultado =
        mictlan_vector2_producto_punto(a, b);

    if (!isfinite(resultado)) {
        latC_error(mv,
            "ciencia.producto_punto2: "
            "resultado fuera de rango");
        return;
    }

    latC_apilar_double(mv, resultado);
}


/* Tabla de funciones del modulo ciencia. */

static const lat_CReg funciones_ciencia[] = {
    {"longitud2", n_ciencia_longitud2, 2},
    {"producto_punto2", n_ciencia_producto_punto2, 4},
    {NULL, NULL, 0}
};


/* Registrar el modulo en la maquina virtual. */
void mictlan_ciencia_ffi_registrar(lat_mv *mv)
{
    if (mv == NULL) {
        return;
    }

    latC_abrir_liblatino(
        mv,
        "ciencia",
        funciones_ciencia
    );
}

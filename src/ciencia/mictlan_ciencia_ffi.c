
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

/* Tabla de funciones del modulo ciencia. */
static const lat_CReg funciones_ciencia[] = {
    {"longitud2", n_ciencia_longitud2, 2},
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


#include "mictlan_graficos_ffi.h"
#include "latmv.h"
#include "latobj.h"

#include <float.h>
#include <math.h>

/*
 * Estado provisional para un unico host activo.
 * No es todavia una API multihilo o multi-VM.
 */
static MictlanLienzo *lienzo_actual = NULL;
static MictlanPlano *plano_actual = NULL;

static bool canal_color_valido(double valor)
{
    return isfinite(valor) &&
           valor >= 0.0 &&
           valor <= 255.0 &&
           floor(valor) == valor;
}

static void n_graficos_circulo(lat_mv *mv)
{
    double azul = latC_checar_numerico(
        mv, latC_desapilar(mv));

    double verde = latC_checar_numerico(
        mv, latC_desapilar(mv));

    double rojo = latC_checar_numerico(
        mv, latC_desapilar(mv));

    double radio = latC_checar_numerico(
        mv, latC_desapilar(mv));

    double y = latC_checar_numerico(
        mv, latC_desapilar(mv));

    double x = latC_checar_numerico(
        mv, latC_desapilar(mv));

    bool coordenadas_validas =
        isfinite(x) &&
        isfinite(y) &&
        isfinite(radio) &&
        fabs(x) <= FLT_MAX &&
        fabs(y) <= FLT_MAX &&
        radio > 0.0 &&
        radio <= FLT_MAX;

    bool colores_validos =
        canal_color_valido(rojo) &&
        canal_color_valido(verde) &&
        canal_color_valido(azul);

    bool correcto = false;

    if (lienzo_actual &&
        coordenadas_validas &&
        colores_validos) {

        correcto = mictlan_lienzo_agregar_circulo(
            lienzo_actual,
            (float)x,
            (float)y,
            (float)radio,
            (unsigned char)rojo,
            (unsigned char)verde,
            (unsigned char)azul,
            255
        );
    }

    latC_apilar(
        mv,
        correcto ? latO_verdadero : latO_falso
    );
}

static void n_graficos_linea(lat_mv *mv)
{
    double v[7];
    for (int i = 6; i >= 0; --i)
        v[i] = latC_checar_numerico(mv, latC_desapilar(mv));
    bool valido = true;
    for (int i = 0; i < 4; ++i)
        valido = valido && isfinite(v[i]) && fabs(v[i]) <= 1.0;
    for (int i = 4; i < 7; ++i)
        valido = valido && canal_color_valido(v[i]);
    if (valido)
        valido = mictlan_plano_agregar_linea(plano_actual, (MictlanLinea){
            (float)v[0], (float)v[1], (float)v[2], (float)v[3],
            (unsigned char)v[4], (unsigned char)v[5], (unsigned char)v[6]});
    latC_apilar(mv, valido ? latO_verdadero : latO_falso);
}

static void n_graficos_limpiar(lat_mv *mv)
{
    if (lienzo_actual) mictlan_lienzo_inicializar(lienzo_actual);
    if (plano_actual) plano_actual->cantidad = 0;
    latC_apilar(mv, lienzo_actual || plano_actual ? latO_verdadero : latO_falso);
}

static const lat_CReg libgraficos[] = {
    {"circulo", n_graficos_circulo, 6},
    {"linea", n_graficos_linea, 7},
    {"limpiar", n_graficos_limpiar, 0},
    {NULL, NULL, 0}
};

void mictlan_graficos_ffi_registrar(
    lat_mv *mv,
    MictlanLienzo *lienzo)
{
    if (!mv || !lienzo) return;

    lienzo_actual = lienzo;
    latC_abrir_liblatino(mv, "graficos", libgraficos);
}

void mictlan_graficos_ffi_conectar_plano(MictlanPlano *plano)
{
    plano_actual = plano;
}

void mictlan_graficos_ffi_desconectar(void)
{
    lienzo_actual = NULL;
    plano_actual = NULL;
}


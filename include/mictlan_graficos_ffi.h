
#ifndef MICTLAN_GRAFICOS_FFI_H
#define MICTLAN_GRAFICOS_FFI_H

#include "latino.h"
#include "mictlan_dibujo2d.h"

/* Conecta el modulo grafico con una VM y un lienzo. */
void mictlan_graficos_ffi_registrar(
    lat_mv *mv,
    MictlanLienzo *lienzo
);

/* Desconecta el lienzo al finalizar la sesion. */
void mictlan_graficos_ffi_desconectar(void);

#endif



#ifndef MICTLAN_DIBUJO2D_H
#define MICTLAN_DIBUJO2D_H

#include <stdbool.h>
#include <stddef.h>

#define MICTLAN_MAX_CIRCULOS 128

typedef struct {
    float x;
    float y;
    float radio;
    unsigned char rojo, verde, azul, alfa;
} MictlanCirculo;

typedef struct {
    MictlanCirculo circulos[MICTLAN_MAX_CIRCULOS];
    size_t cantidad;
} MictlanLienzo;

void mictlan_lienzo_inicializar(MictlanLienzo *lienzo);

bool mictlan_lienzo_agregar_circulo(
    MictlanLienzo *lienzo,
    float x, float y, float radio,
    unsigned char rojo,
    unsigned char verde,
    unsigned char azul,
    unsigned char alfa
);

#endif

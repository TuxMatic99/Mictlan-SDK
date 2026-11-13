
#ifndef MICTLAN_DIBUJO2D_H
#define MICTLAN_DIBUJO2D_H

#include <stdbool.h>
#include <stddef.h>

#define MICTLAN_MAX_CIRCULOS 128
#define MICTLAN_MAX_LINEAS 128

typedef struct {
    float x;
    float y;
    float radio;
    unsigned char rojo, verde, azul, alfa;
} MictlanCirculo;

typedef struct {
    float x1, y1, x2, y2;
    unsigned char rojo, verde, azul;
} MictlanLinea;

typedef struct {
    MictlanCirculo circulos[MICTLAN_MAX_CIRCULOS];
    size_t cantidad;
} MictlanLienzo;

typedef struct {
    MictlanLinea lineas[MICTLAN_MAX_LINEAS];
    size_t cantidad;
} MictlanPlano;

void mictlan_lienzo_inicializar(MictlanLienzo *lienzo);
bool mictlan_plano_agregar_linea(MictlanPlano *plano, MictlanLinea linea);

bool mictlan_lienzo_agregar_circulo(
    MictlanLienzo *lienzo,
    float x, float y, float radio,
    unsigned char rojo,
    unsigned char verde,
    unsigned char azul,
    unsigned char alfa
);

#endif

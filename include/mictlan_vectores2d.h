
#ifndef MICTLAN_VECTORES2D_H
#define MICTLAN_VECTORES2D_H

#include <stdbool.h>

/*
 * Vector bidimensional de precision doble.
 * x = componente horizontal.
 * y = componente vertical.
 */
typedef struct {
    double x;
    double y;
} MictlanVector2;

/* Crear un vector. */
MictlanVector2 mictlan_vector2_crear(double x, double y);

/* Sumar dos vectores. */
MictlanVector2 mictlan_vector2_sumar(
    MictlanVector2 a,
    MictlanVector2 b
);

/* Multiplicar por un escalar. */
MictlanVector2 mictlan_vector2_escalar(
    MictlanVector2 v,
    double factor
);

/* Calcular el producto punto. */
double mictlan_vector2_producto_punto(
    MictlanVector2 a,
    MictlanVector2 b
);

/* Calcular la longitud. */
double mictlan_vector2_longitud(MictlanVector2 v);

/* Normalizar. Devuelve false si no es posible. */
bool mictlan_vector2_normalizar(
    MictlanVector2 v,
    MictlanVector2 *resultado
);

#endif

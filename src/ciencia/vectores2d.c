
#include "mictlan_vectores2d.h"

#include <math.h>
#include <stddef.h>

/* Crear un vector. */
MictlanVector2 mictlan_vector2_crear(double x, double y)
{
    MictlanVector2 v = {x, y};
    return v;
}

/* Suma de dos vectores. */
MictlanVector2 mictlan_vector2_sumar(
    MictlanVector2 a,
    MictlanVector2 b)
{
    return mictlan_vector2_crear(
        a.x + b.x,
        a.y + b.y
    );
}

/* Multiplicacion por un escalar. */
MictlanVector2 mictlan_vector2_escalar(
    MictlanVector2 v,
    double factor)
{
    return mictlan_vector2_crear(
        v.x * factor,
        v.y * factor
    );
}

/* Producto punto. */
double mictlan_vector2_producto_punto(
    MictlanVector2 a,
    MictlanVector2 b)
{
    return a.x * b.x + a.y * b.y;
}

/* Longitud euclidiana. */
double mictlan_vector2_longitud(MictlanVector2 v)
{
    return hypot(v.x, v.y);
}

/* Obtener un vector de longitud uno. */
bool mictlan_vector2_normalizar(
    MictlanVector2 v,
    MictlanVector2 *resultado)
{
    if (resultado == NULL) {
        return false;
    }

    double longitud = mictlan_vector2_longitud(v);

    if (longitud == 0.0 || !isfinite(longitud)) {
        return false;
    }

    resultado->x = v.x / longitud;
    resultado->y = v.y / longitud;

    return true;
}

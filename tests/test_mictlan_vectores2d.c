
#include "mictlan_vectores2d.h"

#include <math.h>
#include <stdio.h>

static int casi_igual(double a, double b)
{
    return isfinite(a) && isfinite(b) &&
           fabs(a - b) < 0.000000001;
}

int main(void)
{
    MictlanVector2 a = mictlan_vector2_crear(3.0, 4.0);
    MictlanVector2 b = mictlan_vector2_crear(1.0, 2.0);

    /* Prueba de suma. */
    MictlanVector2 suma = mictlan_vector2_sumar(a, b);

    if (!casi_igual(suma.x, 4.0) ||
        !casi_igual(suma.y, 6.0)) {
        puts("FALLO: suma de vectores");
        return 1;
    }

    /* Prueba de multiplicacion. */
    MictlanVector2 doble = mictlan_vector2_escalar(a, 2.0);

    if (!casi_igual(doble.x, 6.0) ||
        !casi_igual(doble.y, 8.0)) {
        puts("FALLO: multiplicacion escalar");
        return 1;
    }

    /* Prueba de producto punto. */
    if (!casi_igual(
        mictlan_vector2_producto_punto(a, b), 11.0)) {
        puts("FALLO: producto punto");
        return 1;
    }

    /* Prueba de longitud. */
    if (!casi_igual(mictlan_vector2_longitud(a), 5.0)) {
        puts("FALLO: longitud");
        return 1;
    }

    /* Prueba de normalizacion. */
    MictlanVector2 normalizado = {0.0, 0.0};

    if (!mictlan_vector2_normalizar(a, &normalizado) ||
        !casi_igual(normalizado.x, 0.6) ||
        !casi_igual(normalizado.y, 0.8)) {
        puts("FALLO: normalizacion");
        return 1;
    }

    /* El vector cero no puede normalizarse. */
    MictlanVector2 cero = mictlan_vector2_crear(0.0, 0.0);

    if (mictlan_vector2_normalizar(cero, &normalizado)) {
        puts("FALLO: vector cero");
        return 1;
    }

    puts("OK: suma");
    puts("OK: multiplicacion escalar");
    puts("OK: producto punto");
    puts("OK: longitud");
    puts("OK: normalizacion");
    puts("OK: vector cero protegido");
    puts("MICTLAN_CIENCIA_OK");

    return 0;
}

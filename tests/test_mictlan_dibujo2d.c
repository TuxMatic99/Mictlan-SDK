
#include "mictlan_dibujo2d.h"
#include <stdio.h>

#define COMPROBAR(condicion) do { \
    if (!(condicion)) { \
        fprintf(stderr, "Fallo en linea %d\n", __LINE__); \
        return 1; \
    } \
} while (0)

int main(void)
{
    MictlanLienzo lienzo;

    mictlan_lienzo_inicializar(&lienzo);
    COMPROBAR(lienzo.cantidad == 0);

    COMPROBAR(mictlan_lienzo_agregar_circulo(
        &lienzo, 100, 150, 25, 255, 0, 0, 255
    ));

    COMPROBAR(lienzo.cantidad == 1);
    COMPROBAR(lienzo.circulos[0].x == 100);
    COMPROBAR(lienzo.circulos[0].radio == 25);

    // No aceptar radios negativos.
    COMPROBAR(!mictlan_lienzo_agregar_circulo(
        &lienzo, 100, 150, -5, 255, 0, 0, 255
    ));

    COMPROBAR(lienzo.cantidad == 1);

    // Comprobar limite de capacidad.
    for (int i = 1; i < MICTLAN_MAX_CIRCULOS; i++) {
        COMPROBAR(mictlan_lienzo_agregar_circulo(
            &lienzo, 10, 10, 5, 255, 0, 0, 255
        ));
    }

    COMPROBAR(lienzo.cantidad == MICTLAN_MAX_CIRCULOS);

    COMPROBAR(!mictlan_lienzo_agregar_circulo(
        &lienzo, 10, 10, 5, 255, 0, 0, 255
    ));

    mictlan_lienzo_inicializar(&lienzo);
    COMPROBAR(lienzo.cantidad == 0);

    puts("OK: modulo de dibujo 2D");
    return 0;
}

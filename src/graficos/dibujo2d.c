
#include "mictlan_dibujo2d.h"
#include <math.h>

void mictlan_lienzo_inicializar(MictlanLienzo *lienzo)
{
    if (lienzo == NULL) return;

    lienzo->cantidad = 0;
}

bool mictlan_lienzo_agregar_circulo(
    MictlanLienzo *lienzo,
    float x, float y, float radio,
    unsigned char rojo,
    unsigned char verde,
    unsigned char azul,
    unsigned char alfa
)
{
    if (lienzo == NULL) return false;

    if (lienzo->cantidad >= MICTLAN_MAX_CIRCULOS)
        return false;

    if (!isfinite(x) || !isfinite(y) ||
        !isfinite(radio) || radio <= 0.0f)
        return false;

    MictlanCirculo *circulo =
        &lienzo->circulos[lienzo->cantidad];

    circulo->x = x;
    circulo->y = y;
    circulo->radio = radio;

    circulo->rojo = rojo;
    circulo->verde = verde;
    circulo->azul = azul;
    circulo->alfa = alfa;

    lienzo->cantidad++;

    return true;
}

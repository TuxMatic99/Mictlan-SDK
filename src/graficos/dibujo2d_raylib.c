
#include "mictlan_render_raylib.h"
#include "raylib.h"

void mictlan_renderizar_lienzo(
    const MictlanLienzo *lienzo
)
{
    if (lienzo == NULL) {
        return;
    }

    for (size_t i = 0; i < lienzo->cantidad; i++) {

        const MictlanCirculo *circulo =
            &lienzo->circulos[i];

        Vector2 posicion = {
            circulo->x,
            circulo->y
        };

        Color color = {
            circulo->rojo,
            circulo->verde,
            circulo->azul,
            circulo->alfa
        };

        DrawCircleV(
            posicion,
            circulo->radio,
            color
        );
    }
}

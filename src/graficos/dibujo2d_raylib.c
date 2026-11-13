
#include "mictlan_render_raylib.h"
#include "raylib.h"
#include <math.h>

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

void mictlan_renderizar_lineas(const MictlanPlano *plano, UIRect area)
{
    const float escala = 0.5f * fminf(area.ancho, area.alto) - 4.0f;
    if (!plano || escala <= 0) return;
    const float x = area.x + 0.5f * area.ancho;
    const float y = area.y + 0.5f * area.alto;
    BeginScissorMode((int)area.x, (int)area.y, (int)area.ancho, (int)area.alto);
    for (size_t i = 0; i < plano->cantidad; ++i) {
        const MictlanLinea *l = &plano->lineas[i];
        DrawLineEx((Vector2){x + l->x1 * escala, y - l->y1 * escala},
                   (Vector2){x + l->x2 * escala, y - l->y2 * escala}, 2.5f,
                   (Color){l->rojo, l->verde, l->azul, 255});
    }
    EndScissorMode();
}

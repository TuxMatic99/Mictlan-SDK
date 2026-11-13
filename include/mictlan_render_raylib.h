
#ifndef MICTLAN_RENDER_RAYLIB_H
#define MICTLAN_RENDER_RAYLIB_H

#include "mictlan_dibujo2d.h"
#include "ui_layout.h"

/*
 * Dibuja los círculos registrados.
 * Debe llamarse entre BeginDrawing()
 * y EndDrawing(), con la ventana activa.
 */
void mictlan_renderizar_lienzo(
    const MictlanLienzo *lienzo
);
void mictlan_renderizar_lineas(const MictlanPlano *plano, UIRect area);

#endif
